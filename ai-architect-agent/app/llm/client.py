from __future__ import annotations

import logging
import os

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


class LLMCallException(Exception):
    """Raised when the LLM call fails after all retries are exhausted."""


class LLMClient:
    """Unified LLM client supporting OpenAI and Azure OpenAI providers."""

    def __init__(self) -> None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if provider == "azure":
            self._llm = AzureChatOpenAI(
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                api_version="2024-06-01",
                temperature=0.2,
            )
            logger.info("LLMClient initialized with Azure OpenAI provider")
        else:
            self._llm = ChatOpenAI(
                model="gpt-4o",
                api_key=os.environ.get("OPENAI_API_KEY"),
                temperature=0.2,
            )
            logger.info("LLMClient initialized with OpenAI provider")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(min=1, max=30),
        retry=retry_if_exception_type((TimeoutError, Exception)),
        reraise=True,
    )
    async def _invoke(self, prompt: str) -> object:
        """Invoke the LLM with retry logic."""
        return await self._llm.ainvoke([HumanMessage(content=prompt)])

    async def complete(self, prompt: str, response_format: str = "json") -> str:
        """Call the LLM with the given prompt and return the raw string content.

        Args:
            prompt: The prompt to send to the LLM.
            response_format: If "json", appends instruction to return valid JSON only.

        Returns:
            The raw string content of the LLM response.

        Raises:
            LLMCallException: If the call fails after all retries.
        """
        if response_format == "json":
            prompt = (
                prompt
                + "\n\nIMPORTANT: Return valid JSON only. "
                "No markdown fences, no preamble, no explanation. "
                "Just the raw JSON object."
            )

        try:
            response = await self._invoke(prompt)
        except Exception as e:
            logger.error("LLM call failed after retries: %s", str(e))
            raise LLMCallException(f"LLM call failed: {str(e)}") from e

        content = response.content

        # Strip markdown fences that LLMs sometimes add despite instructions
        if response_format == "json":
            content = self._strip_markdown_fences(content)

        input_tokens = getattr(response, "usage_metadata", {})
        if isinstance(input_tokens, dict):
            logger.debug(
                "LLM tokens — input: %s, output: %s",
                input_tokens.get("input_tokens", "unknown"),
                input_tokens.get("output_tokens", "unknown"),
            )
        else:
            logger.debug("LLM response received (token counts unavailable)")

        return content

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove ```json ... ``` or ``` ... ``` wrappers from LLM output."""
        stripped = text.strip()
        if stripped.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = stripped.index("\n")
            stripped = stripped[first_newline + 1 :]
            # Remove closing fence
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip()[:-3].rstrip()
        return stripped
