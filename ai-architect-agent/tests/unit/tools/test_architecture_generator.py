from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import ArchitectureContext
from app.memory.store import MemoryStore
from app.tools.architecture_generator import ArchitectureGeneratorTool
from app.tools.base import ToolExecutionException


VALID_RESPONSE = json.dumps({
    "style": "event-driven microservices",
    "domain": "fintech",
    "system_type": "payment platform",
    "rationale": "High throughput + decoupled fraud detection requires async event processing",
    "components": [
        {
            "name": "PaymentGateway",
            "type": "service",
            "responsibility": "Accepts and validates incoming payment requests",
            "technology": "Java / Spring Boot",
            "technology_rationale": "Strong typing for financial domain",
            "characteristic_drivers": ["security", "latency"],
            "exposes": ["POST /payments"],
            "depends_on": ["FraudEngine"],
        },
        {
            "name": "FraudEngine",
            "type": "service",
            "responsibility": "Real-time fraud scoring",
            "technology": "Python / FastAPI",
            "technology_rationale": "ML model serving with low latency",
            "characteristic_drivers": ["latency", "security"],
            "exposes": ["fraud.scored event"],
            "depends_on": ["EventBus"],
        },
    ],
    "interactions": [
        {
            "from": "PaymentGateway",
            "to": "FraudEngine",
            "pattern": "async-event",
            "description": "Payment submitted for fraud check",
            "rationale": "Async to avoid blocking the payment flow",
        }
    ],
    "primary_flow": {
        "description": "Process a payment",
        "steps": [
            {"step": 1, "component": "PaymentGateway", "action": "Validate request"},
            {"step": 2, "component": "FraudEngine", "action": "Score transaction"},
        ],
    },
    "characteristic_coverage": {
        "well_addressed": ["latency", "security"],
        "partially_addressed": ["scalability"],
        "deferred": ["observability"],
    },
})


class TestArchitectureGeneratorTool:
    """Tests for ArchitectureGeneratorTool.run()."""

    @pytest.fixture
    def mock_memory(self) -> AsyncMock:
        memory = AsyncMock(spec=MemoryStore)
        memory.retrieve_similar = AsyncMock(return_value=[])
        return memory

    @pytest.fixture
    def tool(self, mock_llm: AsyncMock, mock_memory: AsyncMock) -> ArchitectureGeneratorTool:
        return ArchitectureGeneratorTool(mock_llm, mock_memory)

    @pytest.fixture
    def rich_context(self, base_context: ArchitectureContext) -> ArchitectureContext:
        """Context with characteristics and conflicts already populated."""
        base_context.parsed_entities = {
            "domain": "fintech",
            "system_type": "payment platform",
        }
        base_context.characteristics = [
            {"name": "scalability", "tensions_with": ["cost-efficiency"]},
            {"name": "latency", "tensions_with": ["security"]},
        ]
        base_context.characteristic_conflicts = [
            {"characteristic_a": "latency", "characteristic_b": "security"},
        ]
        base_context.scenarios = [
            {"tier": "medium", "description": "5k TPS normal load"},
        ]
        return base_context

    async def test_writes_architecture_design(
        self, tool, rich_context, mock_llm,
    ):
        """run() writes architecture_design to context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(rich_context)

        assert result.architecture_design["style"] == "event-driven microservices"
        assert len(result.architecture_design["components"]) == 2

    async def test_calls_memory_retrieve(
        self, tool, rich_context, mock_llm, mock_memory,
    ):
        """run() retrieves similar designs from memory store."""
        mock_llm.complete.return_value = VALID_RESPONSE

        await tool.run(rich_context)

        mock_memory.retrieve_similar.assert_awaited_once_with(
            rich_context.raw_requirements, limit=3
        )

    async def test_stores_similar_past_designs(
        self, tool, rich_context, mock_llm, mock_memory,
    ):
        """run() stores retrieved similar designs in context."""
        mock_memory.retrieve_similar.return_value = [
            {"conversation_id": "past-1", "domain": "fintech"},
        ]
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(rich_context)

        assert len(result.similar_past_designs) == 1
        assert result.similar_past_designs[0]["domain"] == "fintech"

    async def test_raises_when_characteristics_empty(
        self, tool, mock_llm,
    ):
        """run() raises ToolExecutionException when characteristics is empty."""
        ctx = ArchitectureContext(raw_requirements="test")

        with pytest.raises(ToolExecutionException, match="characteristics is empty"):
            await tool.run(ctx)

    async def test_raises_on_invalid_json(
        self, tool, rich_context, mock_llm,
    ):
        """run() raises ToolExecutionException on invalid JSON."""
        mock_llm.complete.return_value = "broken json"

        with pytest.raises(ToolExecutionException, match="invalid JSON"):
            await tool.run(rich_context)

    async def test_uses_first_scenario_as_target(
        self, tool, rich_context, mock_llm,
    ):
        """run() passes first scenario as target_scenario in prompt."""
        mock_llm.complete.return_value = VALID_RESPONSE

        await tool.run(rich_context)

        call_args = mock_llm.complete.call_args
        prompt = call_args[0][0]
        assert "5k TPS" in prompt

    async def test_handles_no_scenarios(
        self, tool, rich_context, mock_llm,
    ):
        """run() works when scenarios is empty."""
        rich_context.scenarios = []
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(rich_context)

        assert result.architecture_design["style"] == "event-driven microservices"
