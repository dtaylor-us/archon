from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field
import uuid


class TacticRecommendation(BaseModel):
    """A single architecture tactic recommended for one quality attribute.

    Sourced from Bass, Clements, Kazman "Software Architecture in Practice"
    4th edition (SEI/Addison-Wesley 2021) chapters 4-12, supplemented by
    SEI technical reports.

    A tactic is a focused design decision that influences a single quality
    attribute response. It is NOT an architecture style, technology choice,
    or vague best practice.
    """

    tactic_id: str
    # Sequential identifier e.g. TAC-001

    characteristic_name: str
    # The quality attribute this tactic addresses.
    # Must match a name from ArchitectureContext.characteristics.

    tactic_name: str
    # Canonical name from the Bass/Clements/Kazman catalog.
    # Examples: "Heartbeat", "Active Redundancy", "Parameterise",
    # "Bound Queue Sizes", "Encrypt Data"

    category: str
    # Sub-grouping within the QA tactic set.
    # Examples: "Fault Detection", "Fault Recovery",
    # "Control Resource Demand", "Resist Attacks"

    description: str
    # One sentence: what this tactic does and how it works.
    # Must match the Bass/Clements/Kazman definition.
    # Minimum 20 characters — enforced by TacticsAdvisorTool._validate_tactic.

    concrete_application: str
    # How this tactic applies to THIS specific system.
    # Not generic advice. Must reference actual components from
    # architecture_design.components where possible.
    # Minimum 30 characters — enforced by TacticsAdvisorTool._validate_tactic.

    implementation_examples: list[str]
    # 2-3 concrete, technology-specific examples from the catalog.

    already_addressed: bool
    # True if the current architecture_design already implements
    # this tactic in some form.

    address_evidence: str = ""
    # If already_addressed is True: which component or decision implements it.
    # If False: empty string.

    effort: Literal["low", "medium", "high"]
    # low:    configuration or minor code change
    # medium: new component or significant refactor
    # high:   architectural change or new infrastructure

    priority: Literal["critical", "recommended", "optional"]
    # critical:    directly serves a primary characteristic
    # recommended: serves a secondary characteristic
    # optional:    useful but not essential for this system


class DiagramType(str, Enum):
    """Supported Mermaid diagram types.

    Each value maps to a specific Mermaid syntax keyword.
    """

    C4_CONTAINER = "c4_container"          # graph TD with subgraphs
    SEQUENCE_PRIMARY = "sequence_primary"  # sequenceDiagram happy path
    SEQUENCE_ERROR = "sequence_error"      # sequenceDiagram failure path
    STATE = "state"                        # stateDiagram-v2
    CLASS = "class"                        # classDiagram
    ER = "er"                              # erDiagram
    DEPLOYMENT = "deployment"              # graph TD infra topology
    FLOWCHART = "flowchart"                # flowchart TD decision flow


class Diagram(BaseModel):
    """A single generated Mermaid diagram with metadata.

    The mermaid_source field is preserved verbatim —
    never reformat or summarise it.
    """

    diagram_id: str
    type: DiagramType
    title: str
    description: str
    mermaid_source: str
    # The architecture characteristic this diagram makes visible.
    characteristic_addressed: str = ""


class PipelineMode(str, Enum):
    AUTO = "AUTO"
    ARCHITECTURE_ONLY = "ARCHITECTURE_ONLY"
    TRADE_OFF_ONLY = "TRADE_OFF_ONLY"
    ADL_ONLY = "ADL_ONLY"
    REVIEW_ONLY = "REVIEW_ONLY"


class MessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    TOOL_RESULT = "TOOL_RESULT"


class HistoryMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    created_at: str | None = None


class AdlMetadata(BaseModel):
    """
    Metadata fields for an ADL block.
    These are included in the ADL source but stripped before
    sending to an LLM for code generation per the Richards spec.
    """

    requires: str
    # The tooling needed: ArchUnit, NetArchTest, PyTestArch,
    # or a custom fitness function description.

    description: str
    # Human-readable label for what this block governs.

    prompt: str
    # The LLM instruction that converts this ADL pseudo-code
    # into runnable test code. Must be specific enough that
    # an LLM can produce compilable ArchUnit or equivalent output.


class AdlBlock(BaseModel):
    """
    A single ADL block following Mark Richards' ADL specification.
    Each block governs one specific architectural concern and
    maps directly to one executable fitness function or test.
    """

    adl_id: str
    # Sequential identifier e.g. ADL-001

    metadata: AdlMetadata

    adl_source: str
    # The complete ADL pseudo-code using only valid spec keywords.
    # Must start with DEFINE SYSTEM and contain at least one ASSERT.

    characteristic_enforced: str
    # Which architecture characteristic this block protects.

    enforcement_level: Literal["hard", "soft"] = "soft"
    # hard = CI build must fail on violation
    # soft = warning only


class ArchitectureContext(BaseModel):
    conversation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()))
    iteration: int = 0
    mode: PipelineMode = PipelineMode.AUTO

    raw_requirements: str = ""
    history: list[HistoryMessage] = Field(default_factory=list)

    # Stage outputs — populated phase by phase
    parsed_entities: dict[str, Any] = Field(default_factory=dict)
    missing_requirements: list[dict] = Field(default_factory=list)
    ambiguities: list[dict] = Field(default_factory=list)
    hidden_assumptions: list[dict] = Field(default_factory=list)
    clarifying_questions: list[dict] = Field(default_factory=list)
    scenarios: list[dict] = Field(default_factory=list)

    # Stage 4 — populated by CharacteristicReasoningEngine
    characteristics: list[dict] = Field(default_factory=list)

    # Stage 4b — populated by TacticsAdvisorTool
    # Runs after CharacteristicReasoningEngine, before ConflictAnalyzer.
    # Each entry is a TacticRecommendation serialised to dict via model_dump().
    tactics: list[dict] = Field(default_factory=list)

    tactics_summary: str = ""
    # One paragraph summarising the most important tactics across all
    # characteristics for this system.

    # Stage 5 — populated by CharacteristicConflictAnalyzer
    characteristic_conflicts: list[dict] = Field(default_factory=list)
    underrepresented_characteristics: list[str] = Field(default_factory=list)
    overspecified_characteristics: list[str] = Field(default_factory=list)
    tension_summary: str = ""

    # Stage 6 — populated by ArchitectureGenerator
    architecture_design: dict[str, Any] = Field(default_factory=dict)
    similar_past_designs: list[dict] = Field(default_factory=list)

    # Populated by ArchitectureGeneratorTool — the style selection
    # scoring breakdown used to choose the architecture style.
    # Enables the ReviewAgent to challenge the selection reasoning.
    architecture_style_scores: list[dict] = Field(default_factory=list)

    # Stage 7 — populated by DiagramGeneratorTool
    # Primary storage: typed list of all generated diagrams.
    diagrams: list[Diagram] = Field(default_factory=list)

    # Backward-compatible flat string fields — populated from
    # diagrams list in the tool for any code still reading them.
    mermaid_component_diagram: str = ""
    mermaid_sequence_diagram: str = ""

    # Stage 8 — populated by TradeOffEngine
    trade_offs: list[dict] = Field(default_factory=list)
    trade_off_dominant_tension: str = ""

    # Stage 9 — populated by ADLGeneratorV2Tool
    adl_blocks: list[AdlBlock] = Field(default_factory=list)
    adl_document: str = ""

    # Keep adl_rules as a deprecated alias for backward compatibility
    # with any existing test fixtures — do not remove it
    adl_rules: list[dict] = Field(default_factory=list)

    # Stage 10 — populated by WeaknessAnalyzer
    weaknesses: list[dict] = Field(default_factory=list)
    weakness_summary: str = ""

    # Stage 11 — populated by FMEAPlusTool (runs in parallel with weakness)
    fmea_risks: list[dict] = Field(default_factory=list)
    fmea_critical_risks: list[str] = Field(default_factory=list)

    # Stage 12 — populated by ArchitectReviewAgent
    review_findings: dict[str, Any] = Field(default_factory=dict)
    governance_score: int | None = None
    governance_score_breakdown: dict[str, Any] = Field(default_factory=dict)
    improvement_recommendations: list[dict] = Field(default_factory=list)
    review_constraints: list[str] = Field(default_factory=list)
    should_reiterate: bool = False

    # Cost tracking — populated by LLM client via cost_tracker
    token_usage: dict[str, Any] = Field(default_factory=dict)

    @property
    def selected_architecture_style(self) -> str:
        """Returns the selected architecture style name or empty string."""
        return self.architecture_design.get(
            "style_selection", {}
        ).get("selected_style", "")

    @property
    def is_final_iteration(self) -> bool:
        """True when the pipeline must not re-iterate (max 2 iterations: 0 and 1)."""
        return self.iteration >= 1

    def get_diagram(self, diagram_type: DiagramType) -> str:
        """Return the mermaid_source for the first diagram of the given type.

        Args:
            diagram_type: The DiagramType to search for.

        Returns:
            The mermaid_source string, or empty string if not found.
        """
        for d in self.diagrams:
            if d.type == diagram_type:
                return d.mermaid_source
        return ""

    model_config = {"extra": "allow"}
