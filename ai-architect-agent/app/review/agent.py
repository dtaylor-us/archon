"""Architect Review Agent — a LangGraph sub-graph that stress-tests the architecture.

The review agent operates on a deep copy of the main context data (via ReviewContext)
and never holds a reference to the live ArchitectureContext. Its findings are written
back to the main context after the sub-graph completes.
"""

from __future__ import annotations

import logging

from langgraph.graph import StateGraph, END

from app.llm.client import LLMClient
from app.models import ArchitectureContext
from app.review.context import ReviewContext
from app.review.nodes import (
    ReviewState,
    assumption_challenger,
    trade_off_stress,
    adl_audit,
    governance_scorer,
)

logger = logging.getLogger(__name__)


class ArchitectReviewAgent:
    """Encapsulates the review sub-graph lifecycle.

    Build once at startup, invoke per-pipeline run with a deep copy of context.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client
        self._compiled = self._build_graph()
        logger.info("ArchitectReviewAgent graph compiled")

    @staticmethod
    def _build_graph():
        builder = StateGraph(ReviewState)

        builder.add_node("assumption_challenger", assumption_challenger)
        builder.add_node("trade_off_stress", trade_off_stress)
        builder.add_node("adl_audit", adl_audit)
        builder.add_node("governance_scorer", governance_scorer)

        builder.set_entry_point("assumption_challenger")
        builder.add_edge("assumption_challenger", "trade_off_stress")
        builder.add_edge("trade_off_stress", "adl_audit")
        builder.add_edge("adl_audit", "governance_scorer")
        builder.add_edge("governance_scorer", END)

        return builder.compile()

    def _build_review_context(
        self, context: ArchitectureContext
    ) -> ReviewContext:
        """Create a ReviewContext from a deep copy of main context data."""
        rc = ReviewContext(
            conversation_id=context.conversation_id,
            raw_requirements=context.raw_requirements,
            parsed_entities=context.parsed_entities.copy(),
            characteristics=[c.copy() for c in context.characteristics],
            architecture_design=context.architecture_design.copy(),
            architecture_style_scores=[
                s.copy() for s in context.architecture_style_scores
            ],
            scenarios=[s.copy() for s in context.scenarios],
            trade_offs=[t.copy() for t in context.trade_offs],
            adl_blocks=[
                b.model_dump() if hasattr(b, "model_dump") else b.copy()
                for b in context.adl_blocks
            ],
            weaknesses=[w.copy() for w in context.weaknesses],
            fmea_risks=[r.copy() for r in context.fmea_risks],
        )
        # Inject the LLM client for review nodes to use
        rc._llm_client = self._llm_client  # type: ignore[attr-defined]
        return rc

    async def run(self, context: ArchitectureContext) -> ArchitectureContext:
        """Execute the review sub-graph and write findings back to context.

        Args:
            context: The main pipeline context (NOT mutated during review
                     graph execution — only updated with results at the end).

        Returns:
            Updated ArchitectureContext with review findings populated.
        """
        review_ctx = self._build_review_context(context)

        initial_state: ReviewState = {"review_context": review_ctx}

        # Run the review sub-graph to completion
        result = await self._compiled.ainvoke(initial_state)
        final_rc: ReviewContext = result["review_context"]

        # Write review findings back to the main context
        context.review_findings = {
            "assumption_challenges": [
                c.model_dump() for c in final_rc.assumption_challenges
            ],
            "trade_off_challenges": [
                c.model_dump() for c in final_rc.trade_off_challenges
            ],
            "adl_issues": [
                i.model_dump() for i in final_rc.adl_issues
            ],
            # Preserve existing style_selection_challenge if present
            **(
                {"style_selection_challenge": context.review_findings.get(
                    "style_selection_challenge"
                )}
                if context.review_findings.get("style_selection_challenge")
                else {}
            ),
        }

        context.governance_score = final_rc.governance_score
        if final_rc.governance_score_breakdown:
            context.governance_score_breakdown = (
                final_rc.governance_score_breakdown.model_dump()
            )
        context.improvement_recommendations = [
            r.model_dump() for r in final_rc.improvement_recommendations
        ]
        context.should_reiterate = (
            final_rc.should_reiterate and not context.is_final_iteration
        )

        # Build review constraints for re-iteration
        if context.should_reiterate:
            constraints: list[str] = []
            for r in final_rc.improvement_recommendations:
                if r.requires_reiteration:
                    constraints.append(r.recommendation)
            # Add high-severity trade-off challenges
            for c in final_rc.trade_off_challenges:
                if c.severity == "high":
                    constraints.append(
                        f"Revise trade-off {c.decision_id}: {c.concern}"
                    )
            context.review_constraints = constraints

        logger.info(
            "ArchitectReviewAgent complete: score=%s, reiterate=%s",
            context.governance_score,
            context.should_reiterate,
        )
        return context
