from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncGenerator

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.models import ArchitectureContext
from app.observability import (
    pipeline_span, increment_active_runs, decrement_active_runs,
    record_stage_duration,
)
from app.llm.cost_tracker import start_tracking, get_tracker
from app.pipeline.formatter import format_response
from app.pipeline.nodes import (
    PipelineState,
    requirement_parsing,
    requirement_challenge,
    scenario_modeling,
    characteristic_inference,
    tactics_recommendation,
    conflict_analysis,
    architecture_generation,
    diagram_generation,
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
    "tactics_recommendation",   # stage 4b — after characteristics, before conflicts
    "conflict_analysis",
    "architecture_generation",
    "diagram_generation",
    "trade_off_analysis",
    "adl_generation",
    # Stages 10 and 11 run sequentially in the graph; the asyncio.gather
    # parallelism is handled inside the weakness_analysis node so that
    # FMEA results are available when fmea_analysis emits its event.
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
    "tactics_recommendation": tactics_recommendation,
    "conflict_analysis": conflict_analysis,
    "architecture_generation": architecture_generation,
    "diagram_generation": diagram_generation,
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

    # Track per-stage wall-clock time for metrics
    stage_start_time: float = time.monotonic()

    # Start cost tracking for this pipeline run
    usage_tracker = start_tracking()

    increment_active_runs()
    try:
        async for event in _compiled.astream(initial_state, stream_mode="updates"):
            # event is dict[str, dict] — keys are node names, values are state updates
            for node_name, update in event.items():
                if node_name not in _STAGE_SET:
                    continue

                # Record stage duration from the last STAGE_START to now
                elapsed = time.monotonic() - stage_start_time
                record_stage_duration(node_name, elapsed)

                # Update context from node output
                if "context" in update:
                    context = update["context"]

                # Build enriched payload for STAGE_COMPLETE
                stage_payload: dict = {"status": "complete", "stage": node_name}
                if node_name == "characteristic_inference":
                    stage_payload["characteristic_count"] = len(
                        context.characteristics
                    )
                elif node_name == "tactics_recommendation":
                    stage_payload["tactic_count"] = len(context.tactics)
                    stage_payload["characteristics_covered"] = list({
                        t.get("characteristic_name")
                        for t in context.tactics
                        if t.get("characteristic_name")
                    })
                    stage_payload["already_addressed_count"] = sum(
                        1 for t in context.tactics
                        if t.get("already_addressed")
                    )
                    stage_payload["new_tactics_count"] = sum(
                        1 for t in context.tactics
                        if not t.get("already_addressed")
                    )
                    stage_payload["critical_count"] = sum(
                        1 for t in context.tactics
                        if t.get("priority") == "critical"
                    )
                    stage_payload["tactics_summary"] = context.tactics_summary
                elif node_name == "conflict_analysis":
                    stage_payload["conflict_count"] = len(
                        context.characteristic_conflicts
                    )
                elif node_name == "architecture_generation":
                    stage_payload["style"] = (
                        context.selected_architecture_style
                    )
                    stage_payload["style_scores"] = [
                        {
                            "style": s.get("style"),
                            "score": s.get("score"),
                            "vetoed": s.get("vetoed"),
                        }
                        for s in context.architecture_design.get(
                            "style_selection", {}
                        ).get("style_scores", [])
                    ]
                    stage_payload["runner_up"] = (
                        context.architecture_design.get(
                            "style_selection", {}
                        ).get("runner_up")
                    )
                    stage_payload["component_count"] = len(
                        context.architecture_design.get("components", [])
                    )
                    stage_payload["interaction_count"] = len(
                        context.architecture_design.get("interactions", [])
                    )
                elif node_name == "diagram_generation":
                    stage_payload["diagram_count"] = len(
                        context.diagrams
                    )
                    stage_payload["diagram_types"] = [
                        d.type.value for d in context.diagrams
                    ]
                    stage_payload["diagrams"] = [
                        {
                            "diagram_id": d.diagram_id,
                            "type": d.type.value,
                            "title": d.title,
                            "description": d.description,
                            "source_lines": len(
                                [line for line in
                                 d.mermaid_source.split("\n")
                                 if line.strip()]
                            ),
                        }
                        for d in context.diagrams
                    ]
                elif node_name == "trade_off_analysis":
                    stage_payload["decision_count"] = len(
                        context.trade_offs
                    )
                    stage_payload["dominant_tension"] = (
                        context.trade_off_dominant_tension
                    )
                elif node_name == "adl_generation":
                    stage_payload["block_count"] = len(context.adl_blocks)
                    stage_payload["hard_count"] = sum(
                        1 for b in context.adl_blocks
                        if b.enforcement_level == "hard"
                    )
                    stage_payload["soft_count"] = sum(
                        1 for b in context.adl_blocks
                        if b.enforcement_level == "soft"
                    )
                    stage_payload["characteristics_covered"] = list({
                        b.characteristic_enforced
                        for b in context.adl_blocks
                        if b.characteristic_enforced
                    })
                elif node_name == "weakness_and_fmea":
                    stage_payload["weakness_count"] = len(
                        context.weaknesses
                    )
                    stage_payload["most_critical_weakness"] = (
                        context.weaknesses[0].get("id", "")
                        if context.weaknesses
                        else ""
                    )
                    stage_payload["fmea_risk_count"] = len(
                        context.fmea_risks
                    )
                    stage_payload["critical_risk_count"] = len(
                        context.fmea_critical_risks
                    )
                    stage_payload["top_rpn"] = (
                        context.fmea_risks[0].get("rpn", 0)
                        if context.fmea_risks
                        else 0
                    )
                elif node_name == "architecture_review":
                    stage_payload["governance_score"] = (
                        context.governance_score
                    )
                    stage_payload["governance_score_breakdown"] = (
                        context.governance_score_breakdown
                    )
                    stage_payload["should_reiterate"] = (
                        context.should_reiterate
                    )
                    stage_payload["recommendation_count"] = len(
                        context.improvement_recommendations
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
                    stage_start_time = time.monotonic()
    except Exception as exc:
        logger.error("Pipeline error: %s", str(exc))
        yield _chunk(
            "ERROR",
            content=f"Pipeline error: {str(exc)}",
            payload={"error": str(exc), "conversationId": context.conversation_id},
        )
        return
    finally:
        decrement_active_runs()

    # ── Re-iteration gate ─────────────────────────────────────────
    if context.should_reiterate and not context.is_final_iteration:
        logger.info(
            "Re-iteration triggered (iteration=%d, score=%s)",
            context.iteration,
            context.governance_score,
        )
        yield _chunk(
            "RE_ITERATE",
            conversationId=context.conversation_id,
            payload={
                "iteration": context.iteration,
                "governance_score": context.governance_score,
                "constraints": context.review_constraints,
                "message": "Governance score below threshold — re-iterating pipeline.",
            },
        )

        # Increment iteration and re-run the pipeline
        context.iteration += 1
        async for re_chunk in run_pipeline(context, memory_store=memory_store):
            yield re_chunk
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
            "tactics": context.tactics,
            "tactics_summary": context.tactics_summary,
            "characteristic_conflicts": context.characteristic_conflicts,
            "underrepresented_characteristics": context.underrepresented_characteristics,
            "overspecified_characteristics": context.overspecified_characteristics,
            "tension_summary": context.tension_summary,
            "architecture_design": context.architecture_design,
            "similar_past_designs": context.similar_past_designs,
            "mermaid_component_diagram": context.mermaid_component_diagram,
            "mermaid_sequence_diagram": context.mermaid_sequence_diagram,
            "diagrams": [d.model_dump() for d in context.diagrams],
            "trade_offs": context.trade_offs,
            "trade_off_dominant_tension": context.trade_off_dominant_tension,
            "adl_blocks_generated": len(context.adl_blocks),
            "adl_rules": [b.model_dump() for b in context.adl_blocks],
            "adl_document": context.adl_document,
            "weaknesses": context.weaknesses,
            "weakness_summary": context.weakness_summary,
            "fmea_risks": context.fmea_risks,
            "fmea_critical_risks": context.fmea_critical_risks,
            "review_findings": context.review_findings,
            "governance_score": context.governance_score,
            "governance_score_breakdown": context.governance_score_breakdown,
            "improvement_recommendations": context.improvement_recommendations,
        }.items()
        if v  # only include non-empty fields
    }

    # Attach cost tracking data to context before building COMPLETE payload
    final_tracker = get_tracker()
    if final_tracker is not None:
        context.token_usage = final_tracker.to_dict()

    yield _chunk(
        "COMPLETE",
        conversationId=context.conversation_id,
        payload={
            "message": "Pipeline completed.",
            "stages_executed": len(ORDERED_STAGES),
            "iteration": context.iteration,
            "structured_output": structured,
            "token_usage": context.token_usage,
            "tactics_recommended": len(context.tactics),
            "tactics_already_addressed": sum(
                1 for t in context.tactics if t.get("already_addressed")
            ),
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
