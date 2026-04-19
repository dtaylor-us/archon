from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models import ArchitectureContext
from app.pipeline.nodes import (
    requirement_parsing,
    requirement_challenge,
    scenario_modeling,
    characteristic_inference,
    conflict_analysis,
    architecture_generation,
    diagram_generation,
    trade_off_analysis,
    adl_generation,
    weakness_analysis,
    fmea_analysis,
    architecture_review,
    init_registry,
    PipelineState,
)


@pytest.fixture(autouse=True)
def _setup_registry(mock_llm: AsyncMock):
    """Set up a mock registry for all tests."""
    mock_parser = AsyncMock()
    mock_parser.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_challenge = AsyncMock()
    mock_challenge.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_scenario = AsyncMock()
    mock_scenario.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_char_reasoner = AsyncMock()
    mock_char_reasoner.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_conflict = AsyncMock()
    mock_conflict.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_arch_gen = AsyncMock()
    mock_arch_gen.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_diagram = AsyncMock()
    mock_diagram.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_trade_off = AsyncMock()
    mock_trade_off.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_adl = AsyncMock()
    mock_adl.run = AsyncMock(side_effect=lambda ctx: ctx)

    mock_weakness = AsyncMock()
    mock_weakness.run = AsyncMock(side_effect=lambda ctx: ctx)

    registry = {
        "requirement_parser": mock_parser,
        "challenge_engine": mock_challenge,
        "scenario_modeler": mock_scenario,
        "characteristic_reasoner": mock_char_reasoner,
        "conflict_analyzer": mock_conflict,
        "architecture_generator": mock_arch_gen,
        "diagram_generator": mock_diagram,
        "trade_off_engine": mock_trade_off,
        "adl_generator": mock_adl,
        "weakness_analyzer": mock_weakness,
    }
    init_registry(registry)
    return registry


class TestLiveNodes:
    """Tests for live pipeline nodes (backed by tool calls)."""

    async def test_parse_node_calls_requirement_parser(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """parse_node() calls RequirementParserTool.run() with the context."""
        state: PipelineState = {"context": base_context}

        await requirement_parsing(state)

        _setup_registry["requirement_parser"].run.assert_awaited_once_with(base_context)

    async def test_challenge_node_calls_challenge_engine(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """challenge_node() calls RequirementChallengeEngineTool.run()."""
        state: PipelineState = {"context": base_context}

        await requirement_challenge(state)

        _setup_registry["challenge_engine"].run.assert_awaited_once_with(base_context)

    async def test_scenarios_node_calls_scenario_modeler(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """scenarios_node() calls ScenarioModelerTool.run()."""
        state: PipelineState = {"context": base_context}

        await scenario_modeling(state)

        _setup_registry["scenario_modeler"].run.assert_awaited_once_with(base_context)

    async def test_characteristic_inference_calls_reasoner(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """characteristic_inference() calls CharacteristicReasoningEngineTool.run()."""
        state: PipelineState = {"context": base_context}

        await characteristic_inference(state)

        _setup_registry["characteristic_reasoner"].run.assert_awaited_once_with(base_context)

    async def test_conflict_analysis_calls_analyzer(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """conflict_analysis() calls CharacteristicConflictAnalyzerTool.run()."""
        state: PipelineState = {"context": base_context}

        await conflict_analysis(state)

        _setup_registry["conflict_analyzer"].run.assert_awaited_once_with(base_context)

    async def test_architecture_generation_calls_generator(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """architecture_generation() calls ArchitectureGeneratorTool.run()."""
        state: PipelineState = {"context": base_context}

        await architecture_generation(state)

        _setup_registry["architecture_generator"].run.assert_awaited_once_with(base_context)

    async def test_diagram_generation_calls_diagram_tool(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """diagram_generation() calls DiagramGeneratorTool.run()."""
        state: PipelineState = {"context": base_context}

        await diagram_generation(state)

        _setup_registry["diagram_generator"].run.assert_awaited_once_with(base_context)

    async def test_trade_off_analysis_calls_trade_off_engine(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """trade_off_analysis() calls TradeOffEngineTool.run()."""
        state: PipelineState = {"context": base_context}

        await trade_off_analysis(state)

        _setup_registry["trade_off_engine"].run.assert_awaited_once_with(base_context)

    async def test_adl_generation_calls_adl_generator(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """adl_generation() calls ADLGeneratorV2Tool.run()."""
        state: PipelineState = {"context": base_context}

        await adl_generation(state)

        _setup_registry["adl_generator"].run.assert_awaited_once_with(base_context)

    async def test_weakness_analysis_calls_weakness_analyzer(
        self, base_context: ArchitectureContext, _setup_registry: dict,
    ):
        """weakness_analysis() calls WeaknessAnalyzerTool.run()."""
        state: PipelineState = {"context": base_context}

        await weakness_analysis(state)

        _setup_registry["weakness_analyzer"].run.assert_awaited_once_with(base_context)


class TestStubNodes:
    """Tests for stub pipeline nodes (not yet implemented)."""

    async def test_stub_nodes_return_context_unchanged(
        self, base_context: ArchitectureContext,
    ):
        """Stub nodes return context unchanged."""
        state: PipelineState = {"context": base_context}

        for node_fn in [
            fmea_analysis,
            architecture_review,
        ]:
            result = await node_fn(state)
            assert result["context"] is base_context

    async def test_stub_nodes_do_not_raise(
        self, base_context: ArchitectureContext,
    ):
        """Stub nodes do not raise exceptions."""
        state: PipelineState = {"context": base_context}

        for node_fn in [
            fmea_analysis,
            architecture_review,
        ]:
            # Should complete without raising
            result = await node_fn(state)
            assert "context" in result
