from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock

from app.models import ArchitectureContext
from app.tools.diagram_generator import DiagramGeneratorTool
from app.tools.base import ToolExecutionException


VALID_RESPONSE = json.dumps({
    "component_diagram": (
        "graph TD\n"
        "  subgraph Services\n"
        "    PG[PaymentGateway]\n"
        "    FE[FraudEngine]\n"
        "  end\n"
        "  PG -->|payment.submitted| FE"
    ),
    "sequence_diagram": (
        "sequenceDiagram\n"
        "  PG->>FE: Score transaction\n"
        "  FE-->>PG: fraud result"
    ),
    "diagram_notes": "Simplified for clarity",
})


class TestDiagramGeneratorTool:
    """Tests for DiagramGeneratorTool.run()."""

    @pytest.fixture
    def tool(self, mock_llm: AsyncMock) -> DiagramGeneratorTool:
        return DiagramGeneratorTool(mock_llm)

    @pytest.fixture
    def context_with_design(self, base_context: ArchitectureContext) -> ArchitectureContext:
        """Context with architecture_design already populated."""
        base_context.architecture_design = {
            "style": "event-driven microservices",
            "components": [
                {"name": "PaymentGateway", "type": "service"},
                {"name": "FraudEngine", "type": "service"},
            ],
            "interactions": [
                {"from": "PaymentGateway", "to": "FraudEngine", "pattern": "async-event"},
            ],
            "primary_flow": {
                "description": "Process a payment",
                "steps": [
                    {"step": 1, "component": "PaymentGateway", "action": "Validate request"},
                ],
            },
        }
        return base_context

    async def test_writes_component_diagram(
        self, tool, context_with_design, mock_llm,
    ):
        """run() writes mermaid_component_diagram to context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(context_with_design)

        assert "graph TD" in result.mermaid_component_diagram

    async def test_writes_sequence_diagram(
        self, tool, context_with_design, mock_llm,
    ):
        """run() writes mermaid_sequence_diagram to context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(context_with_design)

        assert "sequenceDiagram" in result.mermaid_sequence_diagram

    async def test_raises_when_design_empty(self, tool, mock_llm):
        """run() raises ToolExecutionException when architecture_design is empty."""
        ctx = ArchitectureContext(raw_requirements="test")

        with pytest.raises(ToolExecutionException, match="architecture_design is empty"):
            await tool.run(ctx)

    async def test_raises_on_invalid_json(
        self, tool, context_with_design, mock_llm,
    ):
        """run() raises ToolExecutionException on invalid JSON."""
        mock_llm.complete.return_value = "broken"

        with pytest.raises(ToolExecutionException, match="invalid JSON"):
            await tool.run(context_with_design)

    async def test_handles_empty_diagrams(
        self, tool, context_with_design, mock_llm,
    ):
        """run() handles LLM returning empty diagram strings."""
        mock_llm.complete.return_value = json.dumps({
            "component_diagram": "",
            "sequence_diagram": "",
            "diagram_notes": "",
        })

        result = await tool.run(context_with_design)

        assert result.mermaid_component_diagram == ""
        assert result.mermaid_sequence_diagram == ""

    async def test_does_not_mutate_architecture_design(
        self, tool, context_with_design, mock_llm,
    ):
        """run() does not mutate the architecture_design field."""
        mock_llm.complete.return_value = VALID_RESPONSE
        original_design = context_with_design.architecture_design.copy()

        await tool.run(context_with_design)

        assert context_with_design.architecture_design == original_design
