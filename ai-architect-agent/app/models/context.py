from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid


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

    # Stage 5 — populated by CharacteristicConflictAnalyzer
    characteristic_conflicts: list[dict] = Field(default_factory=list)
    underrepresented_characteristics: list[str] = Field(default_factory=list)
    overspecified_characteristics: list[str] = Field(default_factory=list)
    tension_summary: str = ""

    # Stage 6 — populated by ArchitectureGenerator
    architecture_design: dict[str, Any] = Field(default_factory=dict)
    similar_past_designs: list[dict] = Field(default_factory=list)

    # Stage 7 — populated by DiagramGenerator
    mermaid_component_diagram: str = ""
    mermaid_sequence_diagram: str = ""
    trade_offs: list[dict] = Field(default_factory=list)
    adl_rules: list[dict] = Field(default_factory=list)
    weaknesses: list[dict] = Field(default_factory=list)
    fmea_risks: list[dict] = Field(default_factory=list)
    review_findings: dict[str, Any] = Field(default_factory=dict)
    governance_score: int | None = None
    should_reiterate: bool = False

    model_config = {"extra": "allow"}
