"""Review agent node functions.

Each node performs one review activity using an LLM call and
writes results into the ReviewContext. Nodes are designed to
run sequentially within the review sub-graph: assumptions and
trade-off stress run first (can be parallel), then ADL audit,
then governance scoring which aggregates all prior findings.
"""

from __future__ import annotations

import json
import logging
from typing import TypedDict

from app.llm.client import LLMClient, set_llm_context
from app.prompts.loader import load_prompt
from app.review.context import (
    AdlIssue,
    AssumptionChallenge,
    GovernanceScoreBreakdown,
    ImprovementRecommendation,
    ReviewContext,
    TradeOffChallenge,
)

logger = logging.getLogger(__name__)


class ReviewState(TypedDict):
    review_context: ReviewContext


async def assumption_challenger(state: ReviewState) -> dict:
    """Challenge hidden assumptions in the architecture design."""
    rc = state["review_context"]
    llm: LLMClient = rc._llm_client  # type: ignore[attr-defined]
    set_llm_context("assumption_challenger", rc.conversation_id)

    prompt = load_prompt(
        "review_assumption_challenger",
        raw_requirements=rc.raw_requirements,
        parsed_entities=rc.parsed_entities,
        architecture_design=rc.architecture_design,
        characteristics=rc.characteristics,
        scenarios=rc.scenarios,
    )

    raw = await llm.complete(prompt, response_format="json")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("assumption_challenger: invalid JSON from LLM")
        return {"review_context": rc}

    challenges = [
        AssumptionChallenge(**c)
        for c in parsed.get("assumption_challenges", [])
        if all(k in c for k in ("assumption", "risk", "recommendation"))
    ]

    rc.assumption_challenges = challenges
    logger.info("assumption_challenger produced %d challenges", len(challenges))
    return {"review_context": rc}


async def trade_off_stress(state: ReviewState) -> dict:
    """Stress-test trade-off decisions against risks and weaknesses."""
    rc = state["review_context"]
    llm: LLMClient = rc._llm_client  # type: ignore[attr-defined]
    set_llm_context("trade_off_stress", rc.conversation_id)

    prompt = load_prompt(
        "review_tradeoff_stress",
        architecture_design=rc.architecture_design,
        trade_offs=rc.trade_offs,
        characteristics=rc.characteristics,
        weaknesses=rc.weaknesses,
        fmea_risks=rc.fmea_risks,
    )

    raw = await llm.complete(prompt, response_format="json")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("trade_off_stress: invalid JSON from LLM")
        return {"review_context": rc}

    challenges = [
        TradeOffChallenge(**c)
        for c in parsed.get("trade_off_challenges", [])
        if all(k in c for k in ("decision_id", "concern", "suggested_revision"))
    ]

    rc.trade_off_challenges = challenges
    logger.info("trade_off_stress produced %d challenges", len(challenges))
    return {"review_context": rc}


async def adl_audit(state: ReviewState) -> dict:
    """Audit ADL blocks for coverage gaps and consistency issues."""
    rc = state["review_context"]
    llm: LLMClient = rc._llm_client  # type: ignore[attr-defined]
    set_llm_context("adl_audit", rc.conversation_id)

    prompt = load_prompt(
        "review_adl_audit",
        adl_blocks=[b if isinstance(b, dict) else b for b in rc.adl_blocks],
        architecture_design=rc.architecture_design,
        characteristics=rc.characteristics,
        weaknesses=rc.weaknesses,
        fmea_risks=rc.fmea_risks,
    )

    raw = await llm.complete(prompt, response_format="json")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("adl_audit: invalid JSON from LLM")
        return {"review_context": rc}

    issues = [
        AdlIssue(**i)
        for i in parsed.get("adl_issues", [])
        if all(k in i for k in ("adl_id", "issue_type", "description", "recommendation"))
    ]

    rc.adl_issues = issues
    logger.info("adl_audit found %d issues", len(issues))
    return {"review_context": rc}


async def governance_scorer(state: ReviewState) -> dict:
    """Compute the overall governance score and improvement recommendations."""
    rc = state["review_context"]
    llm: LLMClient = rc._llm_client  # type: ignore[attr-defined]
    set_llm_context("governance_scorer", rc.conversation_id)

    prompt = load_prompt(
        "review_governance_score",
        raw_requirements=rc.raw_requirements,
        parsed_entities=rc.parsed_entities,
        architecture_design=rc.architecture_design,
        characteristics=rc.characteristics,
        trade_offs=rc.trade_offs,
        adl_blocks=[b if isinstance(b, dict) else b for b in rc.adl_blocks],
        weaknesses=rc.weaknesses,
        fmea_risks=rc.fmea_risks,
        assumption_challenges=[c.model_dump() for c in rc.assumption_challenges],
        trade_off_challenges=[c.model_dump() for c in rc.trade_off_challenges],
        adl_issues=[i.model_dump() for i in rc.adl_issues],
    )

    raw = await llm.complete(prompt, response_format="json")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("governance_scorer: invalid JSON from LLM")
        return {"review_context": rc}

    # Parse score breakdown
    breakdown_data = parsed.get("governance_score_breakdown", {})
    try:
        breakdown = GovernanceScoreBreakdown(**breakdown_data)
        # Ensure total is consistent
        expected_total = (
            breakdown.requirement_coverage
            + breakdown.architectural_soundness
            + breakdown.risk_mitigation
            + breakdown.governance_completeness
        )
        if breakdown.total != expected_total:
            logger.warning(
                "governance_scorer: correcting total %d -> %d",
                breakdown.total,
                expected_total,
            )
            breakdown.total = expected_total
        rc.governance_score_breakdown = breakdown
        rc.governance_score = breakdown.total
    except Exception:
        logger.error("governance_scorer: failed to parse score breakdown")

    # Parse improvement recommendations
    recs = [
        ImprovementRecommendation(**r)
        for r in parsed.get("improvement_recommendations", [])
        if all(k in r for k in ("area", "recommendation"))
    ]
    rc.improvement_recommendations = recs

    # Determine re-iteration need
    rc.should_reiterate = parsed.get("should_reiterate", False)

    logger.info(
        "governance_scorer: score=%d, reiterate=%s, %d recommendations",
        rc.governance_score,
        rc.should_reiterate,
        len(recs),
    )
    return {"review_context": rc}
