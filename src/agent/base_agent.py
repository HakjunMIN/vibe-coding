"""Base Agent implementation using Microsoft Agent Framework.

This module provides a base implementation for AI agents using the Microsoft Agent Framework.
It supports both OpenAI and Azure OpenAI as backends with streaming and non-streaming modes.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from config.agent_config import AgentConfig

# 로거 설정
logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for Agent-related errors."""

    pass


class AgentInitializationError(AgentError):
    """Exception raised when agent initialization fails."""

    pass


class AgentExecutionError(AgentError):
    """Exception raised when agent execution fails."""

    pass


class BaseAgent:
    """Base AI Agent using Microsoft Agent Framework.

    This class provides a high-level interface for interacting with AI models
    through the Microsoft Agent Framework. It supports both Azure OpenAI and
    regular OpenAI backends with streaming capabilities.

    Attributes:
        config: Configuration object containing agent settings.
        chat_client: The chat client (Azure OpenAI or OpenAI).
        agent: The ChatAgent instance from the framework.

    Example:
        >>> from src.config.agent_config import AgentConfig
        >>> config = AgentConfig.from_env()
        >>> agent = BaseAgent(config)
        >>> response = await agent.run("Hello, how are you?")
        >>> print(response)
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the BaseAgent with the given configuration.

        Args:
            config: AgentConfig object containing all necessary settings.

        Raises:
            AgentInitializationError: If agent initialization fails.
        """
        self.config = config
        logger.info(
            "Initializing BaseAgent",
            extra={
                "agent_name": config.agent_name,
                "model": config.model,
                "temperature": config.temperature,
            },
        )

        try:
            # Azure OpenAI 사용 (프로젝트의 AgentConfig가 Azure 전용이므로)
            self.chat_client = self._create_azure_chat_client()
            logger.debug("Created Azure OpenAI chat client")

            # ChatAgent 생성
            self.agent = self._create_chat_agent()
            logger.info("BaseAgent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize BaseAgent: {e}", exc_info=True)
            raise AgentInitializationError(
                f"Failed to initialize agent: {e}"
            ) from e

    def _create_azure_chat_client(self) -> AzureOpenAIChatClient:
        """Create an Azure OpenAI chat client.

        Returns:
            AzureOpenAIChatClient: Configured Azure OpenAI client.

        Raises:
            AgentInitializationError: If client creation fails.
        """
        try:
            # API 키를 사용하는 경우
            client = AzureOpenAIChatClient(
                endpoint=self.config.endpoint,
                deployment_name=self.config.model,
                api_key=self.config.api_key.get_secret_value(),
            )
            return client

        except Exception as e:
            logger.error(f"Failed to create Azure chat client: {e}", exc_info=True)
            raise AgentInitializationError(
                f"Failed to create Azure chat client: {e}"
            ) from e

    def _create_chat_agent(self) -> ChatAgent:
        """Create a ChatAgent instance.

        Returns:
            ChatAgent: Configured agent instance.

        Raises:
            AgentInitializationError: If agent creation fails.
        """
        try:
            instructions = self.config.system_message or "You are a helpful assistant."

            agent = self.chat_client.create_agent(
                name=self.config.agent_name,
                instructions=instructions,
            )

            return agent

        except Exception as e:
            logger.error(f"Failed to create ChatAgent: {e}", exc_info=True)
            raise AgentInitializationError(f"Failed to create ChatAgent: {e}") from e

    async def run(self, message: str) -> str:
        """Process a message and return the agent's response.

        Args:
            message: The user's input message.

        Returns:
            The agent's response as a string.

        Raises:
            AgentExecutionError: If message processing fails.

        Example:
            >>> response = await agent.run("What's the weather like?")
            >>> print(response)
        """
        if not message or not message.strip():
            logger.warning("Empty message provided to run()")
            raise ValueError("Message cannot be empty")

        logger.info(
            "Processing message",
            extra={
                "message_length": len(message),
                "agent_name": self.config.agent_name,
            },
        )

        try:
            result = await self.agent.run(message)

            logger.info(
                "Message processed successfully",
                extra={
                    "response_length": len(str(result)),
                },
            )

            return str(result)

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            raise AgentExecutionError(f"Failed to process message: {e}") from e

    async def run_stream(self, message: str) -> AsyncIterator[str]:
        """Process a message and stream the agent's response.

        Args:
            message: The user's input message.

        Yields:
            Chunks of the agent's response as they are generated.

        Raises:
            AgentExecutionError: If streaming fails.

        Example:
            >>> async for chunk in agent.run_stream("Tell me a story"):
            ...     print(chunk, end="", flush=True)
        """
        if not message or not message.strip():
            logger.warning("Empty message provided to run_stream()")
            raise ValueError("Message cannot be empty")

        logger.info(
            "Starting streaming response",
            extra={
                "message_length": len(message),
                "agent_name": self.config.agent_name,
            },
        )

        try:
            chunk_count = 0
            async for chunk in self.agent.run_stream(message):
                if chunk.text:
                    chunk_count += 1
                    yield chunk.text

            logger.info(
                "Streaming completed",
                extra={
                    "chunk_count": chunk_count,
                },
            )

        except Exception as e:
            logger.error(f"Failed to stream response: {e}", exc_info=True)
            raise AgentExecutionError(f"Failed to stream response: {e}") from e

    def reset(self) -> None:
        """Reset the agent's state.

        This method recreates the ChatAgent to clear conversation history
        and reset the agent to its initial state.

        Raises:
            AgentInitializationError: If agent reset fails.

        Example:
            >>> agent.reset()
            >>> # Agent is now in fresh state with no conversation history
        """
        logger.info("Resetting agent state")

        try:
            self.agent = self._create_chat_agent()
            logger.info("Agent state reset successfully")

        except Exception as e:
            logger.error(f"Failed to reset agent: {e}", exc_info=True)
            raise AgentInitializationError(f"Failed to reset agent: {e}") from e

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """Get the conversation history.

        Returns:
            A list of conversation messages. Each message is a dictionary
            containing message details.

        Note:
            The Microsoft Agent Framework manages thread state internally.
            For persistent threads, use AgentThread with ChatAgent directly.

        Example:
            >>> history = agent.get_conversation_history()
            >>> for msg in history:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        logger.debug("Retrieving conversation history")

        try:
            # Agent Framework의 Thread 관리는 내부적으로 이루어짐
            # 여기서는 빈 리스트를 반환하고, 필요시 AgentThread를 사용하도록 안내
            logger.info(
                "Conversation history requested - "
                "use AgentThread for persistent history management"
            )
            return []

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}", exc_info=True)
            return []
