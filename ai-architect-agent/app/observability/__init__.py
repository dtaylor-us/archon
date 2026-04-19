"""
Observability package for the AI Architect Agent.

Provides OpenTelemetry tracing (spans) and custom metrics
(active runs, token counters, stage duration). Initialised
once at application startup before any other component.
"""

from .tracing import setup_tracing, get_tracer, pipeline_span, llm_span
from .metrics import (
    setup_metrics, increment_active_runs, decrement_active_runs,
    record_tokens, record_stage_duration,
)

__all__ = [
    "setup_tracing", "get_tracer", "pipeline_span", "llm_span",
    "setup_metrics", "increment_active_runs", "decrement_active_runs",
    "record_tokens", "record_stage_duration",
]
