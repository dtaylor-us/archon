from __future__ import annotations

import json
import logging

from app.llm.client import LLMClient
from app.models import ArchitectureContext
from app.prompts.loader import load_prompt
from app.tools.base import BaseTool, ToolExecutionException

logger = logging.getLogger(__name__)


class DiagramGeneratorTool(BaseTool):
    """Generates Mermaid component and sequence diagrams from architecture."""

    async def run(self, context: ArchitectureContext) -> ArchitectureContext:
        if not context.architecture_design:
            raise ToolExecutionException(
                "architecture_design is empty; run ArchitectureGenerator first"
            )

        prompt = load_prompt(
            "diagram_generator",
            architecture_design=context.architecture_design,
        )

        raw = await self.llm_client.complete(prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(
                "DiagramGenerator LLM returned invalid JSON: %s", raw[:500]
            )
            raise ToolExecutionException(
                f"LLM returned invalid JSON: {e}"
            ) from e

        context.mermaid_component_diagram = result.get(
            "component_diagram", ""
        )
        context.mermaid_sequence_diagram = result.get(
            "sequence_diagram", ""
        )
        logger.info(
            "DiagramGenerator produced component diagram (%d chars), "
            "sequence diagram (%d chars)",
            len(context.mermaid_component_diagram),
            len(context.mermaid_sequence_diagram),
        )
        return context
