"""
Base skill class and interface for BookRAGAgent.

Defines the Skill abstraction that all RAG skills inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class Skill(ABC):
    """Base class for all RAG skills."""

    def __init__(self, name: str):
        """
        Initialize skill.

        Args:
            name: Skill name for logging
        """
        self.name = name

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Execute the skill.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Skill output
        """
        pass

    async def __call__(self, *args, **kwargs) -> Any:
        """Allow skill to be called as a function."""
        logger.debug(f"Executing skill: {self.name}")
        return await self.execute(*args, **kwargs)
