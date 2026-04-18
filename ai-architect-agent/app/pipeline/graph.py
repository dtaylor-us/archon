from __future__ import annotations

import logging
from typing import AsyncGenerator

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.models import ArchitectureContext
from app.pipeline.nodes import (
    PipelineState,
    requirement_parsing,
    requirement_challenge,
    scenario_modeling,
    characteristic_inference,
    conflict_analysis,
    architecture_generation,
    trade_off_analysis,
    adl_generation,
    weakness_analysis,
    fmea_analysis,
    architecture_review,
)

logger = logging.getLogger(__name__)

# Ordered list of pipeline stages — determines execution order and edge topology
ORDERED_STAGES: list[str] = [
    "requirement_parsing",
    "requirement_challenge",
    "scenario_modeling",
    "characteristic_inference",
    "conflict_analysis",
    "architecture_generation",
    "trade_off_analysis",
    "adl_generation",
    "weakness_analysis",
    "fmea_analysis",
    "architecture_review",
]

_STAGE_SET: set[str] = set(ORDERED_STAGES)

_NODE_FN_MAP = {
    "requirement_parsing": requirement_parsing,
    "requirement_challenge": requirement_challenge,
    "scenario_modeling": scenario_modeling,
    "characteristic_inference": characteristic_inference,
    "conflict_analysis": conflict_analysis,
    "architecture_generation": architecture_generation,
    "trade_off_analysis": trade_off_analysis,
    "adl_generation": adl_generation,
    "weakness_analysis": weakness_analysis,
    "fmea_analysis": fmea_analysis,
    "architecture_review": architecture_review,
}

# Compiled graph — set once via compile_pipeline()
_compiled = None


# -------------------------------------------------------------------
# NDJSON chunk helpers (mirrors agent.py's chunk format)
# -------------------------------------------------------------------

class _Chunk(BaseModel):
    type: str
    content: str | None = None
    stage: str | None = None
    toolName: str | None = None
    payload: dict | None = None
    conversationId: str | None = None
    metadata: dict | None = None


def _chunk(event_type: str, **kwargs: object) -> str:
    data = _Chunk(type=event_type, **kwargs)
    return data.model_dump_json(exclude_none=True) + "\n"


# -------------------------------------------------------------------
# Graph construction
# -------------------------------------------------------------------

def compile_pipeline() -> None:
    """Build the LangGraph StateGraph and compile it (called once at startup)."""
    global _compiled

    builder = StateGraph(PipelineState)

    for name, fn in _NODE_FN_MAP.items():
        builder.add_node(name, fn)

    builder.set_entry_point(ORDERED_STAGES[0])

    for i in range(len(ORDERED_STAGES) - 1):
        builder.add_edge(ORDERED_STAGES[i], ORDERED_STAGES[i + 1])

    builder.add_edge(ORDERED_STAGES[-1], END)

    _compiled = builder.compile()
    logger.info("Pipeline graph compiled with %d stages", len(ORDERED_STAGES))


# -------------------------------------------------------------------
# Streaming execution
# -------------------------------------------------------------------

async def run_pipeline(
    context: ArchitectureContext,
) -> AsyncGenerator[str, None]:
    """Execute the full pipeline and yield NDJSON chunks as stages progress.

    Yields:
        NDJSON strings — one per line — following the STAGE_START / STAGE_COMPLETE /
        COMPLETE event protocol defined in ARCHITECTURE.md.
    """
    if _compiled is None:
        raise RuntimeError("Pipeline graph not compiled — call compile_pipeline() first")

    initial_state: PipelineState = {"context": context}

    # Emit STAGE_START for the first stage before graph execution begins
    yield _chunk("STAGE_START", stage=ORDERED_STAGES[0])

    try:
        async for event in _compiled.astream(initial_state, stream_mode="updates"):
            # event is dict[str, dict] — keys are node names, values are state updates
            for node_name, update in event.items():
                if node_name not in _STAGE_SET:
                    continue

                # Update context from node output
                if "context" in update:
                    context = update["context"]

                yield _chunk(
                    "STAGE_COMPLETE",
                    stage=node_name,
                    payload={"status": "complete", "stage": node_name},
                )

                # Emit STAGE_START for the next stage if there is one
                idx = ORDERED_STAGES.index(node_name)
                if idx + 1 < len(ORDERED_STAGES):
                    yield _chunk("STAGE_START", stage=ORDERED_STAGES[idx + 1])
    except Exception as exc:
        logger.error("Pipeline error: %s", str(exc))
        yield _chunk(
            "ERROR",
            content=f"Pipeline error: {str(exc)}",
            payload={"error": str(exc), "conversationId": context.conversation_id},
        )
        return

    yield _chunk(
        "COMPLETE",
        conversationId=context.conversation_id,
        payload={
            "message": "Pipeline completed.",
            "stages_executed": len(ORDERED_STAGES),
            "iteration": context.iteration,
        },
    )
