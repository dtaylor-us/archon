from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.models import ArchitectureContext
from app.pipeline.formatter import format_response
from app.pipeline.nodes import (
    PipelineState,
    requirement_parsing,
    requirement_challenge,
    scenario_modeling,
    characteristic_inference,
    conflict_analysis,
    architecture_generation,
    diagram_generation,
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
    "diagram_generation",
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
    "diagram_generation": diagram_generation,
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
    memory_store: object | None = None,
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

                # Build enriched payload for STAGE_COMPLETE
                stage_payload: dict = {"status": "complete", "stage": node_name}
                if node_name == "characteristic_inference":
                    stage_payload["characteristic_count"] = len(
                        context.characteristics
                    )
                elif node_name == "conflict_analysis":
                    stage_payload["conflict_count"] = len(
                        context.characteristic_conflicts
                    )
                elif node_name == "architecture_generation":
                    stage_payload["component_count"] = len(
                        context.architecture_design.get("components", [])
                    )
                    stage_payload["style"] = context.architecture_design.get(
                        "style", ""
                    )
                elif node_name == "diagram_generation":
                    stage_payload["component_diagram_length"] = len(
                        context.mermaid_component_diagram
                    )
                    stage_payload["sequence_diagram_length"] = len(
                        context.mermaid_sequence_diagram
                    )

                yield _chunk(
                    "STAGE_COMPLETE",
                    stage=node_name,
                    payload=stage_payload,
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

    # Emit the formatted architecture report as CHUNK content
    report = format_response(context)
    yield _chunk("CHUNK", content=report)

    # Build structured output for persistence
    structured = {
        k: v for k, v in {
            "parsed_entities": context.parsed_entities,
            "missing_requirements": context.missing_requirements,
            "ambiguities": context.ambiguities,
            "hidden_assumptions": context.hidden_assumptions,
            "clarifying_questions": context.clarifying_questions,
            "scenarios": context.scenarios,
            "characteristics": context.characteristics,
            "characteristic_conflicts": context.characteristic_conflicts,
            "underrepresented_characteristics": context.underrepresented_characteristics,
            "overspecified_characteristics": context.overspecified_characteristics,
            "tension_summary": context.tension_summary,
            "architecture_design": context.architecture_design,
            "similar_past_designs": context.similar_past_designs,
            "mermaid_component_diagram": context.mermaid_component_diagram,
            "mermaid_sequence_diagram": context.mermaid_sequence_diagram,
            "trade_offs": context.trade_offs,
            "adl_rules": context.adl_rules,
            "weaknesses": context.weaknesses,
            "fmea_risks": context.fmea_risks,
            "review_findings": context.review_findings,
            "governance_score": context.governance_score,
        }.items()
        if v  # only include non-empty fields
    }

    yield _chunk(
        "COMPLETE",
        conversationId=context.conversation_id,
        payload={
            "message": "Pipeline completed.",
            "stages_executed": len(ORDERED_STAGES),
            "iteration": context.iteration,
            "structured_output": structured,
        },
    )

    # Fire-and-forget: store design in Qdrant for future similarity lookups
    if memory_store and context.architecture_design:
        asyncio.create_task(_store_design_safe(
            memory_store, context,
        ))


async def _store_design_safe(
    memory_store: object, context: ArchitectureContext,
) -> None:
    """Best-effort background store — never raises."""
    try:
        await memory_store.store_design(  # type: ignore[attr-defined]
            conversation_id=context.conversation_id,
            requirements=context.raw_requirements,
            architecture_design=context.architecture_design,
            characteristics=context.characteristics,
        )
    except Exception:
        logger.warning("Failed to store design after pipeline", exc_info=True)
