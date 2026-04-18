from __future__ import annotations

import json
import logging

from app.llm.client import LLMClient
from app.memory.store import MemoryStore
from app.models import ArchitectureContext
from app.prompts.loader import load_prompt
from app.tools.base import BaseTool, ToolExecutionException

logger = logging.getLogger(__name__)


class ArchitectureGeneratorTool(BaseTool):
    """Generates a full architecture design driven by inferred characteristics."""

    def __init__(
        self, llm_client: LLMClient, memory_store: MemoryStore
    ) -> None:
        super().__init__(llm_client)
        self._memory = memory_store

    async def run(self, context: ArchitectureContext) -> ArchitectureContext:
        if not context.characteristics:
            raise ToolExecutionException(
                "characteristics is empty; run CharacteristicReasoningEngine first"
            )

        # Retrieve similar past designs from Qdrant (best-effort)
        similar = await self._memory.retrieve_similar(
            context.raw_requirements, limit=3
        )
        context.similar_past_designs = similar

        # Pick a representative scenario as the target
        target_scenario = (
            context.scenarios[0] if context.scenarios else {}
        )

        prompt = load_prompt(
            "architecture_generator",
            raw_requirements=context.raw_requirements,
            parsed_entities=context.parsed_entities,
            characteristics=context.characteristics,
            characteristic_conflicts=context.characteristic_conflicts,
            target_scenario=target_scenario,
            similar_past_designs=similar,
        )

        raw = await self.llm_client.complete(prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(
                "ArchitectureGenerator LLM returned invalid JSON: %s",
                raw[:500],
            )
            raise ToolExecutionException(
                f"LLM returned invalid JSON: {e}"
            ) from e

        context.architecture_design = result
        logger.info(
            "ArchitectureGenerator produced design with %d components, style=%s",
            len(result.get("components", [])),
            result.get("style", "unknown"),
        )
        return context
