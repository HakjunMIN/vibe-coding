"""Configuration models for the Vibe Coding agent."""

from __future__ import annotations

import os
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator


class AgentConfig(BaseModel):
    """AI Agent configuration model.

    Validates runtime parameters for the agent and supports loading them from environment variables.

    Attributes:
        agent_name: Human-friendly agent identifier.
        model: Deployment name for Azure OpenAI.
        temperature: Sampling temperature between 0.0 and 2.0.
        max_tokens: Maximum tokens allowed per completion.
        api_key: Azure OpenAI API key wrapped in ``SecretStr``.
        endpoint: Azure OpenAI endpoint URL.
        timeout: Request timeout in seconds.
        system_message: Optional system prompt for the agent.
    """

    _TEMPERATURE_MIN: ClassVar[float] = 0.0
    _TEMPERATURE_MAX: ClassVar[float] = 2.0
    _MAX_TOKENS_MIN: ClassVar[int] = 1
    _MAX_TOKENS_MAX: ClassVar[int] = 32_000
    _MAX_MESSAGE_LENGTH_MIN: ClassVar[int] = 1
    _MAX_MESSAGE_LENGTH_MAX: ClassVar[int] = 10_000
    _MAX_CONTEXT_MESSAGES_MIN: ClassVar[int] = 1
    _MAX_CONTEXT_MESSAGES_MAX: ClassVar[int] = 100
    _MAX_RETRIES_MIN: ClassVar[int] = 1
    _MAX_RETRIES_MAX: ClassVar[int] = 10
    _TIMEOUT_MIN: ClassVar[int] = 1
    _TIMEOUT_MAX: ClassVar[int] = 300

    agent_name: str = Field(default="VibeCodingAgent", description="Agent name")
    model: str = Field(
        default="gpt-4",
        description="Azure OpenAI deployment name",
    )
    temperature: float = Field(
        default=0.7,
        description="LLM sampling temperature",
    )
    max_tokens: int = Field(default=2_000, description="Maximum tokens per response")
    max_message_length: int = Field(
        default=4_000, description="Maximum length of input messages"
    )
    max_context_messages: int = Field(
        default=20, description="Maximum number of messages to keep in context"
    )
    model_name: str = Field(
        default="gpt-4", description="Model name for context management"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retry attempts for API calls"
    )
    api_key: SecretStr = Field(description="Azure OpenAI API key")
    endpoint: str = Field(description="Azure OpenAI endpoint URL")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    system_message: str | None = Field(
        default=None,
        description="Optional system message for the agent",
    )

    @field_validator("temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        """Ensure ``temperature`` stays within the supported range."""
        if not cls._TEMPERATURE_MIN <= value <= cls._TEMPERATURE_MAX:
            raise ValueError(
                f"temperature must be between {cls._TEMPERATURE_MIN} and {cls._TEMPERATURE_MAX}"
            )
        return value

    @field_validator("max_tokens")
    @classmethod
    def _validate_max_tokens(cls, value: int) -> int:
        """Ensure ``max_tokens`` stays within the supported range."""
        if not cls._MAX_TOKENS_MIN <= value <= cls._MAX_TOKENS_MAX:
            raise ValueError(
                f"max_tokens must be between {cls._MAX_TOKENS_MIN} and {cls._MAX_TOKENS_MAX}"
            )
        return value

    @field_validator("max_message_length")
    @classmethod
    def _validate_max_message_length(cls, value: int) -> int:
        """Ensure ``max_message_length`` stays within the supported range."""
        if not cls._MAX_MESSAGE_LENGTH_MIN <= value <= cls._MAX_MESSAGE_LENGTH_MAX:
            raise ValueError(
                f"max_message_length must be between {cls._MAX_MESSAGE_LENGTH_MIN} and {cls._MAX_MESSAGE_LENGTH_MAX}"
            )
        return value

    @field_validator("max_context_messages")
    @classmethod
    def _validate_max_context_messages(cls, value: int) -> int:
        """Ensure ``max_context_messages`` stays within the supported range."""
        if not cls._MAX_CONTEXT_MESSAGES_MIN <= value <= cls._MAX_CONTEXT_MESSAGES_MAX:
            raise ValueError(
                f"max_context_messages must be between {cls._MAX_CONTEXT_MESSAGES_MIN} and {cls._MAX_CONTEXT_MESSAGES_MAX}"
            )
        return value

    @field_validator("max_retries")
    @classmethod
    def _validate_max_retries(cls, value: int) -> int:
        """Ensure ``max_retries`` stays within the supported range."""
        if not cls._MAX_RETRIES_MIN <= value <= cls._MAX_RETRIES_MAX:
            raise ValueError(
                f"max_retries must be between {cls._MAX_RETRIES_MIN} and {cls._MAX_RETRIES_MAX}"
            )
        return value

    @field_validator("timeout")
    @classmethod
    def _validate_timeout(cls, value: int) -> int:
        """Ensure ``timeout`` stays within the supported range."""
        if not cls._TIMEOUT_MIN <= value <= cls._TIMEOUT_MAX:
            raise ValueError(
                f"timeout must be between {cls._TIMEOUT_MIN} and {cls._TIMEOUT_MAX}"
            )
        return value

    @classmethod
    def from_env(cls) -> AgentConfig:
        """Build an ``AgentConfig`` instance from environment variables.

        Loads environment variables from .env file if present, then from system environment.

        Returns:
            AgentConfig: Configuration populated from environment variables.

        Raises:
            ValueError: If required Azure OpenAI environment variables are missing or invalid.
            ValidationError: If any value violates validation constraints.
        """
        # .env 파일에서 환경 변수 로드
        load_dotenv()

        api_key = os.getenv("AZURE_OPENAI_KEY")
        if api_key is None or api_key.strip() == "":
            raise ValueError("AZURE_OPENAI_KEY environment variable is required")

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if endpoint is None or endpoint.strip() == "":
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")

        try:
            return cls(
                agent_name=os.getenv("AGENT_NAME", "VibeCodingAgent"),
                model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4"),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
                max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4000")),
                max_context_messages=int(os.getenv("MAX_CONTEXT_MESSAGES", "20")),
                model_name=os.getenv("MODEL_NAME", "gpt-4"),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                api_key=api_key,
                endpoint=endpoint,
                timeout=int(os.getenv("TIMEOUT", "60")),
                system_message=os.getenv("SYSTEM_MESSAGE"),
            )
        except ValidationError:
            raise
        except ValueError as exc:  # pragma: no cover - re-raise with context
            raise ValidationError(
                [
                    {
                        "loc": ("from_env",),
                        "msg": str(exc),
                        "type": "value_error",
                    }
                ],
                cls,
            ) from exc
