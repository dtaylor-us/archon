from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.models import ArchitectureContext
from app.tools.base import ToolExecutionException


INTERNAL_SECRET = "test-secret-for-integration"
VALID_HEADERS = {"x-internal-secret": INTERNAL_SECRET}


@pytest.fixture
def mock_registry():
    """Build a mock tool registry that returns contexts unchanged.

    Each mock wires .execute() → .run() to match the production
    BaseTool.execute() delegation pattern used by pipeline nodes.
    """
    def _make_tool():
        tool = AsyncMock()
        tool.run = AsyncMock(side_effect=lambda ctx: ctx)

        async def _exec(ctx, _t=tool):
            return await _t.run(ctx)

        tool.execute = AsyncMock(side_effect=_exec)
        return tool

    return {
        "requirement_parser": _make_tool(),
        "challenge_engine": _make_tool(),
        "scenario_modeler": _make_tool(),
        "characteristic_reasoner": _make_tool(),
        "conflict_analyzer": _make_tool(),
        "architecture_generator": _make_tool(),
        "diagram_generator": _make_tool(),
        "trade_off_engine": _make_tool(),
        "adl_generator": _make_tool(),
        "weakness_analyzer": _make_tool(),
        "fmea_analyzer": _make_tool(),
    }


@pytest.fixture
async def test_app(mock_llm, mock_registry):
    """Create a test FastAPI app with mocked LLM and registry."""
    with patch.dict(os.environ, {"INTERNAL_SECRET": INTERNAL_SECRET}):
        # We need to patch the pipeline compile and registry init
        from app.pipeline.nodes import init_registry, init_review_agent
        from app.pipeline.graph import compile_pipeline

        init_registry(mock_registry)

        # Create a mock review agent that returns context unchanged
        mock_review_agent = MagicMock()
        mock_review_agent.run = AsyncMock(side_effect=lambda ctx: ctx)
        init_review_agent(mock_review_agent)

        compile_pipeline()

        from app.main import app
        app.state.llm_client = mock_llm
        app.state.tool_registry = mock_registry
        yield app


@pytest.fixture
async def client(test_app) -> AsyncClient:
    """Create an httpx AsyncClient for the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAgentStreamEndpoint:
    """Integration tests for POST /agent/stream."""

    async def test_returns_401_without_secret(self, client: AsyncClient):
        """POST /agent/stream without X-Internal-Secret returns 401."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "test"},
        )
        assert response.status_code == 401

    async def test_returns_401_with_wrong_secret(self, client: AsyncClient):
        """POST /agent/stream with wrong secret returns 401."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "test"},
            headers={"x-internal-secret": "wrong-secret"},
        )
        assert response.status_code == 401

    async def test_returns_ndjson_content_type(self, client: AsyncClient):
        """POST /agent/stream with valid secret returns application/x-ndjson."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build a payment system"},
            headers=VALID_HEADERS,
        )
        assert response.status_code == 200
        assert "application/x-ndjson" in response.headers["content-type"]

    async def test_stream_contains_stage_start_for_requirement_parsing(
        self, client: AsyncClient,
    ):
        """Response stream contains STAGE_START event for requirement_parsing."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build a payment system"},
            headers=VALID_HEADERS,
        )
        lines = [
            json.loads(line) for line in response.text.strip().split("\n") if line.strip()
        ]
        stage_starts = [
            e for e in lines if e.get("type") == "STAGE_START"
            and e.get("stage") == "requirement_parsing"
        ]
        assert len(stage_starts) >= 1

    async def test_stream_contains_stage_complete_for_each_stage(
        self, client: AsyncClient,
    ):
        """Response stream contains STAGE_COMPLETE event for each stage."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build a payment system"},
            headers=VALID_HEADERS,
        )
        lines = [
            json.loads(line) for line in response.text.strip().split("\n") if line.strip()
        ]
        stage_completes = [e for e in lines if e.get("type") == "STAGE_COMPLETE"]
        # Should have at least one STAGE_COMPLETE per pipeline stage (11 stages)
        assert len(stage_completes) >= 11

    async def test_stream_ends_with_complete_event(self, client: AsyncClient):
        """Response stream ends with COMPLETE event."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build a payment system"},
            headers=VALID_HEADERS,
        )
        lines = [
            json.loads(line) for line in response.text.strip().split("\n") if line.strip()
        ]
        assert lines[-1]["type"] == "COMPLETE"

    async def test_complete_payload_contains_conversation_id(
        self, client: AsyncClient,
    ):
        """COMPLETE payload contains conversationId."""
        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build a payment system"},
            headers=VALID_HEADERS,
        )
        lines = [
            json.loads(line) for line in response.text.strip().split("\n") if line.strip()
        ]
        complete = [e for e in lines if e.get("type") == "COMPLETE"]
        assert len(complete) == 1
        assert complete[0]["conversationId"] == "c1"

    async def test_tool_exception_emits_error_event(
        self, client: AsyncClient, mock_registry: dict,
    ):
        """If a tool raises ToolExecutionException, stream emits ERROR event."""
        mock_registry["requirement_parser"].run = AsyncMock(
            side_effect=ToolExecutionException("parse failed")
        )

        response = await client.post(
            "/agent/stream",
            json={"conversationId": "c1", "userMessage": "Build something"},
            headers=VALID_HEADERS,
        )
        assert response.status_code == 200
        lines = [
            json.loads(line) for line in response.text.strip().split("\n") if line.strip()
        ]
        error_events = [e for e in lines if e.get("type") == "ERROR"]
        assert len(error_events) >= 1
        assert "parse failed" in error_events[0].get("content", "")
