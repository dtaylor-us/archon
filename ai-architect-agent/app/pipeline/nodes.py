from __future__ import annotations

import asyncio
import logging
from typing import TypedDict

from app.models import ArchitectureContext
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Module-level registry — set once during app startup via init_registry()
_registry: dict[str, BaseTool] | None = None


def init_registry(registry: dict[str, BaseTool]) -> None:
    """Set the module-level tool registry (called once at startup)."""
    global _registry
    _registry = registry


class PipelineState(TypedDict):
    context: ArchitectureContext


# ---------------------------------------------------------------------------
# Live tool nodes (backed by real LLM calls)
# ---------------------------------------------------------------------------

async def requirement_parsing(state: PipelineState) -> dict:
    ctx = await _registry["requirement_parser"].run(state["context"])
    return {"context": ctx}


async def requirement_challenge(state: PipelineState) -> dict:
    ctx = await _registry["challenge_engine"].run(state["context"])
    return {"context": ctx}


async def scenario_modeling(state: PipelineState) -> dict:
    ctx = await _registry["scenario_modeler"].run(state["context"])
    return {"context": ctx}


# ---------------------------------------------------------------------------
# Stub nodes — placeholders for later phases
# ---------------------------------------------------------------------------

async def _stub_node(state: PipelineState) -> dict:
    """Pass-through stub for stages not yet implemented."""
    await asyncio.sleep(0.05)
    return {"context": state["context"]}


async def characteristic_inference(state: PipelineState) -> dict:
    ctx = await _registry["characteristic_reasoner"].run(state["context"])
    return {"context": ctx}


async def conflict_analysis(state: PipelineState) -> dict:
    ctx = await _registry["conflict_analyzer"].run(state["context"])
    return {"context": ctx}


async def architecture_generation(state: PipelineState) -> dict:
    ctx = await _registry["architecture_generator"].run(state["context"])
    return {"context": ctx}


async def diagram_generation(state: PipelineState) -> dict:
    ctx = await _registry["diagram_generator"].run(state["context"])
    return {"context": ctx}


async def trade_off_analysis(state: PipelineState) -> dict:
    ctx = await _registry["trade_off_engine"].run(state["context"])
    return {"context": ctx}


async def adl_generation(state: PipelineState) -> dict:
    ctx = await _registry["adl_generator"].run(state["context"])
    return {"context": ctx}


async def weakness_analysis(state: PipelineState) -> dict:
    ctx = await _registry["weakness_analyzer"].run(state["context"])
    return {"context": ctx}


async def fmea_analysis(state: PipelineState) -> dict:
    return await _stub_node(state)


async def architecture_review(state: PipelineState) -> dict:
    """Run the review agent and challenge the style selection.

    The ReviewAgent stress-tests the architecture style selection
    by checking consistency with the top characteristics, validating
    veto decisions, and evaluating whether the large-scale scenario
    would break the selected style.
    """
    ctx = state["context"]
    ctx = _challenge_style_selection(ctx)
    await asyncio.sleep(0.05)
    return {"context": ctx}


def _challenge_style_selection(
    context: ArchitectureContext,
) -> ArchitectureContext:
    """Validate style selection against top characteristics and scenarios.

    Produces a style_selection_challenge entry in review_findings.
    This runs as part of the architecture_review node — it never
    mutates forward-pass fields, only review_findings.

    Args:
        context: The pipeline context after architecture generation.

    Returns:
        Context with review_findings["style_selection_challenge"] populated.
    """
    style_selection = context.architecture_design.get("style_selection", {})
    selected = style_selection.get("selected_style", "")
    style_scores = style_selection.get("style_scores", [])

    challenge: dict = {
        "challenged": False,
        "reason": "",
        "recommended_alternative": None,
    }

    if not selected or not style_scores:
        challenge["challenged"] = True
        challenge["reason"] = (
            "Style selection data is missing — cannot validate."
        )
        context.review_findings["style_selection_challenge"] = challenge
        return context

    # 1. Is the selected style consistent with the top 3 characteristics?
    top_characteristics = [
        c.get("name", "").lower()
        for c in context.characteristics[:3]
    ]
    selected_entry = next(
        (s for s in style_scores if s.get("style") == selected), None
    )
    if selected_entry and top_characteristics:
        driving = {
            d.lower()
            for d in selected_entry.get("driving_characteristics", [])
        }
        if top_characteristics[0] and top_characteristics[0] not in driving:
            challenge["challenged"] = True
            challenge["reason"] = (
                f"Top characteristic '{top_characteristics[0]}' is not "
                f"in the driving_characteristics of selected style "
                f"'{selected}'."
            )

    # 2. Check for improperly vetoed styles
    for score_entry in style_scores:
        if score_entry.get("vetoed") and not score_entry.get("veto_reason"):
            challenge["challenged"] = True
            challenge["reason"] += (
                f" Style '{score_entry.get('style')}' was vetoed "
                f"without a reason."
            )

    # 3. Would the large-scale scenario break the selected style?
    large_scenarios = [
        s for s in context.scenarios
        if s.get("tier", "").lower() == "large"
    ]
    if large_scenarios and selected.lower() in (
        "layered", "layered (n-tier)", "modular monolith",
        "microkernel", "pipeline",
    ):
        challenge["challenged"] = True
        large_desc = large_scenarios[0].get("description", "")
        challenge["reason"] += (
            f" Large-scale scenario ('{large_desc[:80]}') may exceed "
            f"the capacity of monolithic style '{selected}'."
        )
        # Suggest the runner-up as the alternative
        runner_up = style_selection.get("runner_up", "")
        if runner_up:
            challenge["recommended_alternative"] = runner_up

    challenge["reason"] = challenge["reason"].strip()
    context.review_findings["style_selection_challenge"] = challenge
    return context
