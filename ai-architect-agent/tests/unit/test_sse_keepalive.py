"""
Unit tests for keepalive comment emission during pipeline execution.

The agent emits keepalive comment lines to prevent idle timeout disconnects
when long-running stages produce no NDJSON events for an extended period.
"""

from __future__ import annotations

import asyncio

import pytest

from app.models import ArchitectureContext
from app.pipeline import graph as pipeline_graph


class _FakeCompiledGraph:
    """Test double for LangGraph compiled pipeline."""

    def __init__(self, gate: asyncio.Event, ctx: ArchitectureContext) -> None:
        self._gate = gate
        self._ctx = ctx

    async def astream(self, initial_state, stream_mode: str = "updates"):
        # Do not yield any stage updates until gate is opened.
        await self._gate.wait()
        yield {"requirement_parsing": {"context": self._ctx}}


@pytest.mark.asyncio
async def test_run_pipeline_emits_heartbeat_comments_during_stage_execution(monkeypatch):
    """Heartbeat comments must be emitted before a long stage completes."""
    ctx = ArchitectureContext(conversation_id="c1", raw_requirements="r1")
    gate = asyncio.Event()

    monkeypatch.setattr(pipeline_graph, "_compiled", _FakeCompiledGraph(gate, ctx))
    monkeypatch.setattr(pipeline_graph, "HEARTBEAT_INTERVAL_SECONDS", 0.01)

    gen = pipeline_graph.run_pipeline(ctx)

    first = await asyncio.wait_for(gen.__anext__(), timeout=0.2)
    assert '"type":"STAGE_START"' in first

    heartbeat = await asyncio.wait_for(gen.__anext__(), timeout=0.2)
    assert heartbeat.startswith(": heartbeat")

    await gen.aclose()


@pytest.mark.asyncio
async def test_heartbeat_task_is_cancelled_after_pipeline_completes(monkeypatch):
    """Heartbeat task must stop after pipeline completes."""
    ctx = ArchitectureContext(conversation_id="c1", raw_requirements="r1")
    gate = asyncio.Event()
    gate.set()

    monkeypatch.setattr(pipeline_graph, "_compiled", _FakeCompiledGraph(gate, ctx))
    monkeypatch.setattr(pipeline_graph, "HEARTBEAT_INTERVAL_SECONDS", 0.01)

    gen = pipeline_graph.run_pipeline(ctx)

    # Drain a few items until StopAsyncIteration. If the heartbeat continues after
    # completion, this loop would keep yielding comment lines.
    drained = 0
    try:
        while drained < 50:
            await asyncio.wait_for(gen.__anext__(), timeout=0.2)
            drained += 1
    except StopAsyncIteration:
        return

    pytest.fail("Pipeline generator did not terminate as expected")

