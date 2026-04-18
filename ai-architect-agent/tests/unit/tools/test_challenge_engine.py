from __future__ import annotations

import json

import pytest
from unittest.mock import AsyncMock

from app.models import ArchitectureContext
from app.tools.challenge_engine import RequirementChallengeEngineTool
from app.tools.base import ToolExecutionException


VALID_RESPONSE = json.dumps({
    "missing_requirements": [
        {
            "area": "authentication",
            "description": "No auth strategy specified",
            "impact_if_ignored": "Security vulnerability",
        }
    ],
    "ambiguities": [
        {
            "term": "real-time",
            "context": "real-time processing",
            "possible_interpretations": ["sub-second", "sub-100ms"],
        }
    ],
    "hidden_assumptions": [
        {
            "assumption": "Single region deployment",
            "risk_if_wrong": "Latency for global users",
        }
    ],
    "clarifying_questions": [
        {
            "question": "What is the expected peak TPS?",
            "references": "missing load profile",
            "blocks_decision": "capacity planning",
        },
        {
            "question": "Which currencies must be supported?",
            "references": "multi-currency requirement",
            "blocks_decision": "data model design",
        },
        {
            "question": "What is the SLA target?",
            "references": "availability requirement",
            "blocks_decision": "architecture tier selection",
        },
        {
            "question": "Who are the primary users?",
            "references": "user personas",
            "blocks_decision": "UX architecture",
        },
        {
            "question": "Is there a compliance audit requirement?",
            "references": "regulatory gap",
            "blocks_decision": "logging architecture",
        },
    ],
})


class TestRequirementChallengeEngineTool:
    """Tests for RequirementChallengeEngineTool.run()."""

    @pytest.fixture
    def tool(self, mock_llm: AsyncMock) -> RequirementChallengeEngineTool:
        return RequirementChallengeEngineTool(mock_llm)

    @pytest.fixture
    def context_with_entities(self, base_context: ArchitectureContext) -> ArchitectureContext:
        """Context with parsed_entities already populated."""
        base_context.parsed_entities = {"domain": "fintech", "system_type": "payment platform"}
        return base_context

    async def test_writes_missing_requirements(
        self, tool: RequirementChallengeEngineTool, context_with_entities: ArchitectureContext,
        mock_llm: AsyncMock,
    ):
        """run() writes missing_requirements to context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(context_with_entities)

        assert len(result.missing_requirements) == 1
        assert result.missing_requirements[0]["area"] == "authentication"

    async def test_writes_clarifying_questions(
        self, tool: RequirementChallengeEngineTool, context_with_entities: ArchitectureContext,
        mock_llm: AsyncMock,
    ):
        """run() writes clarifying_questions to context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(context_with_entities)

        assert len(result.clarifying_questions) == 5
        assert "TPS" in result.clarifying_questions[0]["question"]

    async def test_raises_on_invalid_json(
        self, tool: RequirementChallengeEngineTool, context_with_entities: ArchitectureContext,
        mock_llm: AsyncMock,
    ):
        """run() raises ToolExecutionException on invalid JSON response."""
        mock_llm.complete.return_value = "not json"

        with pytest.raises(ToolExecutionException, match="invalid JSON"):
            await tool.run(context_with_entities)

    async def test_raises_when_parsed_entities_empty(
        self, tool: RequirementChallengeEngineTool, base_context: ArchitectureContext,
    ):
        """run() raises ToolExecutionException when parsed_entities is empty."""
        base_context.parsed_entities = {}

        with pytest.raises(ToolExecutionException, match="parsed_entities is empty"):
            await tool.run(base_context)

    async def test_writes_ambiguities_and_hidden_assumptions(
        self, tool: RequirementChallengeEngineTool, context_with_entities: ArchitectureContext,
        mock_llm: AsyncMock,
    ):
        """run() populates ambiguities and hidden_assumptions on context."""
        mock_llm.complete.return_value = VALID_RESPONSE

        result = await tool.run(context_with_entities)

        assert len(result.ambiguities) == 1
        assert result.ambiguities[0]["term"] == "real-time"
        assert len(result.hidden_assumptions) == 1
