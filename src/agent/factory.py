"""Agent Factory for creating and managing ChatAgent instances.

This module provides a Singleton factory for creating ChatAgent instances
with proper configuration and caching support.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

from config.agent_config import AgentConfig

# 로거 설정
logger = logging.getLogger(__name__)


class AgentFactory:
    """Singleton factory for creating and managing ChatAgent instances.

    This factory implements the Singleton pattern to ensure only one instance exists.
    It provides caching for ChatAgent instances based on their configuration,
    allowing reuse of agents with identical settings.

    Attributes:
        _instance: Singleton instance of the factory.
        _agent_cache: Dictionary caching ChatAgent instances by configuration hash.

    Example:
        >>> factory = AgentFactory()
        >>> config = AgentConfig.from_env()
        >>> agent = await factory.create_agent(config)
        >>> # Or create directly from environment variables
        >>> agent = await factory.create_from_env()
    """

    _instance: ClassVar[AgentFactory | None] = None
    _agent_cache: dict[str, ChatAgent]

    def __new__(cls) -> AgentFactory:
        """Create or return the singleton instance.

        Returns:
            AgentFactory: The singleton instance of the factory.
        """
        if cls._instance is None:
            logger.info("AgentFactory 싱글톤 인스턴스를 생성합니다")
            cls._instance = super().__new__(cls)
            cls._instance._agent_cache = {}
        return cls._instance

    def _get_cache_key(self, config: AgentConfig) -> str:
        """Generate a cache key from configuration.

        Args:
            config: Agent configuration to generate key from.

        Returns:
            String hash representing the configuration.
        """
        # Azure OpenAI 설정을 기반으로 캐시 키 생성
        return f"{config.endpoint}:{config.model}:{config.temperature}:{config.max_tokens}"

    def _validate_config(self, config: AgentConfig) -> None:
        """Validate agent configuration.

        Args:
            config: Agent configuration to validate.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not config.endpoint:
            raise ValueError("Azure OpenAI endpoint는 필수입니다")

        if not config.api_key:
            raise ValueError("Azure OpenAI API key는 필수입니다")

        if not config.model:
            raise ValueError("Azure OpenAI deployment name은 필수입니다")

        logger.debug(
            "설정 검증 완료",
            extra={
                "endpoint": config.endpoint,
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
        )

    async def create_agent(self, config: AgentConfig) -> ChatAgent:
        """Create a ChatAgent instance with the given configuration.

        This method creates a new ChatAgent or returns a cached instance if
        an agent with identical configuration already exists.

        Args:
            config: Agent configuration containing model, endpoint, and other settings.

        Returns:
            ChatAgent: Configured ChatAgent instance ready for use.

        Raises:
            ValueError: If the configuration is invalid.

        Example:
            >>> factory = AgentFactory()
            >>> config = AgentConfig(
            ...     model="gpt-4",
            ...     api_key="your-key",
            ...     endpoint="https://your-resource.openai.azure.com"
            ... )
            >>> agent = await factory.create_agent(config)
        """
        # 설정 검증
        self._validate_config(config)

        # 캐시 확인
        cache_key = self._get_cache_key(config)
        if cache_key in self._agent_cache:
            logger.info(
                "캐시된 Agent 인스턴스를 반환합니다",
                extra={"cache_key": cache_key},
            )
            return self._agent_cache[cache_key]

        logger.info(
            "새로운 ChatAgent 인스턴스를 생성합니다",
            extra={
                "model": config.model,
                "endpoint": config.endpoint,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            },
        )

        # Azure OpenAI 클라이언트 생성
        try:
            chat_client = AzureOpenAIChatClient(
                model=config.model,
                azure_endpoint=config.endpoint,
                api_key=config.api_key.get_secret_value(),
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

            # ChatAgent 생성
            agent = ChatAgent(
                chat_client=chat_client,
                instructions=config.system_message or "You are a helpful assistant.",
                name=config.agent_name,
            )

            # 캐시에 저장
            self._agent_cache[cache_key] = agent

            logger.info(
                "ChatAgent 생성 완료",
                extra={
                    "agent_name": config.agent_name,
                    "cache_key": cache_key,
                },
            )

            return agent

        except Exception as exc:
            logger.error(
                "ChatAgent 생성 실패",
                extra={
                    "error": str(exc),
                    "model": config.model,
                    "endpoint": config.endpoint,
                },
                exc_info=True,
            )
            raise ValueError(f"ChatAgent 생성 실패: {exc}") from exc

    async def create_from_env(self) -> ChatAgent:
        """Create a ChatAgent instance from environment variables.

        This is a convenience method that loads configuration from environment
        variables and creates an agent.

        Returns:
            ChatAgent: Configured ChatAgent instance.

        Raises:
            ValueError: If required environment variables are missing or invalid.

        Example:
            >>> # .env 파일에 설정이 있다고 가정
            >>> factory = AgentFactory()
            >>> agent = await factory.create_from_env()
        """
        logger.info("환경 변수에서 Agent 설정을 로드합니다")

        try:
            config = AgentConfig.from_env()
            return await self.create_agent(config)
        except ValueError as exc:
            logger.error(
                "환경 변수에서 설정 로드 실패",
                extra={"error": str(exc)},
                exc_info=True,
            )
            raise

    def clear_cache(self) -> None:
        """Clear all cached agent instances.

        This method removes all cached ChatAgent instances, forcing new
        instances to be created on the next request.

        Example:
            >>> factory = AgentFactory()
            >>> factory.clear_cache()
        """
        cache_size = len(self._agent_cache)
        self._agent_cache.clear()
        logger.info(
            "Agent 캐시를 클리어했습니다",
            extra={"cleared_count": cache_size},
        )

    def get_cache_size(self) -> int:
        """Get the number of cached agent instances.

        Returns:
            Number of cached ChatAgent instances.

        Example:
            >>> factory = AgentFactory()
            >>> size = factory.get_cache_size()
            >>> print(f"캐시된 Agent 수: {size}")
        """
        return len(self._agent_cache)
