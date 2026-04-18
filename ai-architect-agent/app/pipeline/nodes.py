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
    return await _stub_node(state)


async def conflict_analysis(state: PipelineState) -> dict:
    return await _stub_node(state)


async def architecture_generation(state: PipelineState) -> dict:
    return await _stub_node(state)


async def trade_off_analysis(state: PipelineState) -> dict:
    return await _stub_node(state)


async def adl_generation(state: PipelineState) -> dict:
    return await _stub_node(state)


async def weakness_analysis(state: PipelineState) -> dict:
    return await _stub_node(state)


async def fmea_analysis(state: PipelineState) -> dict:
    return await _stub_node(state)


async def architecture_review(state: PipelineState) -> dict:
    return await _stub_node(state)
