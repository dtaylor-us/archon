from __future__ import annotations

from app.llm.client import LLMClient
from app.tools.base import BaseTool
from app.tools.requirement_parser import RequirementParserTool
from app.tools.challenge_engine import RequirementChallengeEngineTool
from app.tools.scenario_modeler import ScenarioModelerTool


def build_registry(llm_client: LLMClient) -> dict[str, BaseTool]:
    """Build and return the tool registry mapping tool names to instances.

    Args:
        llm_client: The shared LLM client instance.

    Returns:
        Dict mapping tool name strings to initialized tool instances.
    """
    return {
        "requirement_parser": RequirementParserTool(llm_client),
        "challenge_engine": RequirementChallengeEngineTool(llm_client),
        "scenario_modeler": ScenarioModelerTool(llm_client),
    }
