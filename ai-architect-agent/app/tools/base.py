from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.llm.client import LLMClient
from app.models import ArchitectureContext


class ToolExecutionException(Exception):
    """Raised when a pipeline tool fails during execution."""


class BaseTool(ABC):
    """Abstract base class for all pipeline tools."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    @abstractmethod
    async def run(self, context: ArchitectureContext) -> ArchitectureContext:
        """Execute the tool against the given context.

        Args:
            context: The full pipeline context to read from and write to.

        Returns:
            The mutated ArchitectureContext with this tool's output fields populated.
        """
        ...

    def name(self) -> str:
        """Return the class name in snake_case."""
        class_name = self.__class__.__name__
        # Remove trailing "Tool" if present for cleaner names
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
