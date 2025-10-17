"""LLM 응답 생성을 담당하는 모듈."""

import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from agent_framework import ChatAgent, ChatMessage
from agent_framework.azure import AzureOpenAIChatClient

from config.agent_config import AgentConfig

logger = logging.getLogger(__name__)


class ResponseGenerationError(Exception):
    """응답 생성 관련 예외."""

    pass


class ResponseGenerator:
    """LLM 응답 생성을 담당하는 클래스.

    Microsoft Agent Framework의 ChatAgent를 사용하여 응답을 생성합니다.

    Attributes:
        config: Agent 설정
        chat_agent: ChatAgent 인스턴스
        token_usage: 토큰 사용량 추적
        cache: 응답 캐시

    Example:
        >>> config = AgentConfig()
        >>> generator = ResponseGenerator(config)
        >>> messages = [ChatMessage(role="user", text="안녕하세요")]
        >>> response = await generator.generate(messages)
    """

    def __init__(self, config: AgentConfig) -> None:
        """ResponseGenerator를 초기화합니다.

        Args:
            config: Agent 설정
        """
        self.config = config
        self.token_usage: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self.cache: dict[str, str] = {}

        # ChatClient 초기화
        self.chat_client = AzureOpenAIChatClient(
            endpoint=self.config.endpoint,
            deployment_name=config.model,
            api_key=self.config.api_key.get_secret_value()
        )

        # ChatAgent 초기화
        self.chat_agent = ChatAgent(
            chat_client=self.chat_client,
            instructions=config.system_message,
        )

        logger.info(
            "ResponseGenerator 초기화",
            extra={"model": config.model_name, "max_retries": config.max_retries},
        )

    def _get_cache_key(self, messages: list[ChatMessage]) -> str:
        """메시지 리스트의 캐시 키를 생성합니다.

        Args:
            messages: 메시지 리스트

        Returns:
            캐시 키 (해시값)
        """
        messages_str = json.dumps(
            [{"role": str(msg.role), "text": msg.text} for msg in messages],
            sort_keys=True,
        )
        return hashlib.md5(messages_str.encode()).hexdigest()

    async def _retry_with_backoff(
        self, func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Exponential backoff으로 재시도합니다.

        Args:
            func: 실행할 비동기 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            함수 실행 결과

        Raises:
            ResponseGenerationError: 모든 재시도 실패 시
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"재시도 {attempt + 1}/{self.config.max_retries}",
                        extra={"wait_time": wait_time, "error": str(e)},
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "모든 재시도 실패",
                        extra={"attempts": self.config.max_retries, "error": str(e)},
                    )

        raise ResponseGenerationError(
            f"응답 생성 실패: {last_exception}"
        ) from last_exception

    def _update_token_usage(self, usage: dict[str, int] | None) -> None:
        """토큰 사용량을 업데이트합니다.

        Args:
            usage: 토큰 사용량 정보
        """
        if usage:
            self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            self.token_usage["total_tokens"] += usage.get("total_tokens", 0)

    async def generate(self, messages: list[ChatMessage]) -> str:
        """메시지 리스트로부터 응답을 생성합니다.

        Args:
            messages: 대화 메시지 리스트

        Returns:
            생성된 응답 텍스트

        Raises:
            ResponseGenerationError: 응답 생성 실패 시

        Example:
            >>> messages = [ChatMessage(role="user", text="날씨가 어때?")]
            >>> response = await generator.generate(messages)
            >>> isinstance(response, str)
            True
        """
        # 캐시 확인
        cache_key = self._get_cache_key(messages)
        if cache_key in self.cache:
            logger.info("캐시에서 응답 반환", extra={"cache_key": cache_key})
            return self.cache[cache_key]

        async def _generate() -> str:
            """내부 생성 함수."""
            result = await self.chat_agent.run(messages=messages)

            # 토큰 사용량 업데이트
            if hasattr(result, "usage"):
                self._update_token_usage(result.usage)

            # 응답 추출
            if hasattr(result, "text"):
                response = result.text
            elif hasattr(result, "content"):
                response = result.content
            else:
                response = str(result)
            return response

        try:
            response = await self._retry_with_backoff(_generate)

            # 캐시 저장
            self.cache[cache_key] = response

            logger.info(
                "응답 생성 완료",
                extra={
                    "message_count": len(messages),
                    "response_length": len(response),
                    "token_usage": self.token_usage,
                },
            )

            return response

        except Exception as e:
            logger.error("응답 생성 실패", extra={"error": str(e)})
            raise ResponseGenerationError(f"응답 생성 중 오류 발생: {e}") from e

    async def generate_stream(
        self, messages: list[ChatMessage]
    ) -> AsyncIterator[str]:
        """스트리밍 방식으로 응답을 생성합니다.

        Args:
            messages: 대화 메시지 리스트

        Yields:
            생성된 토큰 문자열

        Raises:
            ResponseGenerationError: 응답 생성 실패 시

        Example:
            >>> messages = [ChatMessage(role="user", text="이야기를 들려줘")]
            >>> async for token in generator.generate_stream(messages):
            ...     print(token, end="", flush=True)
        """
        async def _generate_stream() -> AsyncIterator[str]:
            """내부 스트리밍 생성 함수."""
            stream = await self.chat_agent.run_stream(messages=messages)

            async for chunk in stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk

        try:
            logger.info("스트리밍 응답 생성 시작", extra={"message_count": len(messages)})

            token_count = 0
            async for token in self._retry_with_backoff(_generate_stream):
                token_count += 1
                yield token

            logger.info(
                "스트리밍 응답 생성 완료", extra={"token_count": token_count}
            )

        except Exception as e:
            logger.error("스트리밍 응답 생성 실패", extra={"error": str(e)})
            raise ResponseGenerationError(
                f"스트리밍 응답 생성 중 오류 발생: {e}"
            ) from e

    async def generate_with_tools(
        self, messages: list[ChatMessage], tools: list[Any]
    ) -> str:
        """도구를 사용하여 응답을 생성합니다.

        Args:
            messages: 대화 메시지 리스트
            tools: 사용 가능한 도구 리스트

        Returns:
            생성된 응답 텍스트

        Raises:
            ResponseGenerationError: 응답 생성 실패 시

        Example:
            >>> def get_weather(location: str) -> str:
            ...     return f"{location}의 날씨는 맑습니다"
            >>> messages = [ChatMessage(role="user", text="서울 날씨는?")]
            >>> response = await generator.generate_with_tools(messages, [get_weather])
        """
        async def _generate_with_tools() -> str:
            """내부 도구 사용 생성 함수."""
            # 도구를 포함한 ChatAgent 생성
            agent_with_tools = ChatAgent(
                chat_client=self.chat_client,
                instructions=self.config.system_message,
                tools=tools,
            )

            result = await agent_with_tools.run(messages=messages)

            # 토큰 사용량 업데이트
            if hasattr(result, "usage"):
                self._update_token_usage(result.usage)

            response = result.content if hasattr(result, "content") else str(result)
            return response

        try:
            response = await self._retry_with_backoff(_generate_with_tools)

            logger.info(
                "도구 사용 응답 생성 완료",
                extra={
                    "message_count": len(messages),
                    "tool_count": len(tools),
                    "response_length": len(response),
                },
            )

            return response

        except Exception as e:
            logger.error("도구 사용 응답 생성 실패", extra={"error": str(e)})
            raise ResponseGenerationError(
                f"도구 사용 응답 생성 중 오류 발생: {e}"
            ) from e

    def get_token_usage(self) -> dict[str, int]:
        """현재까지의 토큰 사용량을 반환합니다.

        Returns:
            토큰 사용량 딕셔너리

        Example:
            >>> usage = generator.get_token_usage()
            >>> usage["total_tokens"] >= 0
            True
        """
        return self.token_usage.copy()

    def clear_cache(self) -> None:
        """응답 캐시를 초기화합니다.

        Example:
            >>> generator.clear_cache()
            >>> len(generator.cache)
            0
        """
        self.cache.clear()
        logger.info("응답 캐시 초기화됨")
