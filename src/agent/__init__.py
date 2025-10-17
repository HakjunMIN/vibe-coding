"""Agent module for vibe-coding-agent.

This module provides AI Agent implementations using Microsoft Agent Framework.
"""

from .base_agent import (
    AgentError,
    AgentExecutionError,
    AgentInitializationError,
    BaseAgent,
)
from .factory import AgentFactory

__all__ = [
    "BaseAgent",
    "AgentFactory",
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError",
]
__version__ = "0.1.0"
__author__ = "Vibe Coding Team"
