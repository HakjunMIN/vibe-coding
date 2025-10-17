"""모든 컴포넌트를 통합하는 대화형 Agent."""

import logging
import time
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

from agent_framework import ChatMessage

from .base_agent import BaseAgent
from config.agent_config import AgentConfig
from .context_manager import ContextManager
from .message_processor import MessageProcessor
from .models import Conversation, Message
from .response_generator import ResponseGenerator

logger = logging.getLogger(__name__)


class ConversationAgent(BaseAgent):
    """모든 컴포넌트를 통합하여 대화를 처리하는 Agent.

    MessageProcessor, ResponseGenerator, ContextManager를 조합하여
    완전한 대화 파이프라인을 제공합니다. Microsoft Agent Framework의
    도구 시스템을 지원하여 함수 호출 기능을 사용할 수 있습니다.

    Attributes:
        config: Agent 설정
        message_processor: 메시지 전처리 및 검증
        response_generator: LLM 응답 생성
        context_manager: 대화 컨텍스트 관리
        conversation: 현재 대화
        tools: 사용 가능한 도구 함수 리스트
        metrics: 성능 메트릭

    Example:
        >>> from src.agent.tools.web_search import search_web
        >>> config = AgentConfig()
        >>> agent = ConversationAgent(config, tools=[search_web])
        >>> response = await agent.chat("Search for Python tutorials")
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        message_processor: MessageProcessor | None = None,
        response_generator: ResponseGenerator | None = None,
        context_manager: ContextManager | None = None,
        conversation: Conversation | None = None,
        tools: list[Callable[..., Any]] | None = None,
    ) -> None:
        """ConversationAgent를 초기화합니다.

        Args:
            config: Agent 설정 (None이면 기본값 사용)
            message_processor: 메시지 프로세서 (None이면 생성)
            response_generator: 응답 생성기 (None이면 생성)
            context_manager: 컨텍스트 매니저 (None이면 생성)
            conversation: 대화 모델 (None이면 생성)
            tools: 사용할 도구 함수 리스트 (None이면 도구 없이 동작)
        """
        super().__init__(config or AgentConfig())

        # 도구 설정
        self.tools = tools or []

        # 컴포넌트 초기화 (의존성 주입 또는 기본값)
        self.message_processor = message_processor or MessageProcessor(
            max_length=self.config.max_message_length,
        )
        self.response_generator = response_generator or ResponseGenerator(
            self.config
        )
        self.context_manager = context_manager or ContextManager(
            max_messages=self.config.max_context_messages,
            model_name=self.config.model_name,
        )
        self.conversation = conversation or Conversation()

        # 성능 메트릭
        self.metrics: dict[str, float | int] = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
            "tool_calls": 0,
        }

        logger.info(
            "ConversationAgent 초기화 완료",
            extra={
                "model": self.config.model_name,
                "max_context_messages": self.config.max_context_messages,
                "tools_count": len(self.tools),
            },
        )

    async def chat(self, user_message: str, tools: list[Callable[..., Any]] | None = None) -> str:
        """사용자 메시지를 받아 응답을 반환합니다.

        전체 파이프라인:
        1. 메시지 전처리 및 검증
        2. 컨텍스트에 추가
        3. LLM 응답 생성 (필요시 도구 호출)
        4. 응답 후처리
        5. 메트릭 업데이트

        Args:
            user_message: 사용자 메시지
            tools: 이 대화에서만 사용할 도구 (None이면 Agent 레벨 도구 사용)

        Returns:
            Agent의 응답

        Raises:
            ValueError: 메시지 검증 실패
            ResponseGenerationError: 응답 생성 실패

        Example:
            >>> # Agent 레벨 도구 사용
            >>> response = await agent.chat("Search for Python tutorials")
            
            >>> # Run 레벨 도구 사용
            >>> from src.agent.tools.web_search import search_web
            >>> response = await agent.chat("Search for AI news", tools=[search_web])
        """
        start_time = time.time()
        active_tools = tools if tools is not None else self.tools

        try:
            # 1. 메시지 전처리
            logger.info("메시지 전처리 시작", extra={"message_length": len(user_message)})
            processed_message = self.message_processor.preprocess(user_message)

            # 2. 메시지 검증
            self.message_processor.validate(processed_message)

            # 3. 의도 추출 (선택적)
            intent = self.message_processor.extract_intent(processed_message)
            logger.debug("의도 추출 완료", extra={"intent": intent})

            # 4. 컨텍스트에 사용자 메시지 추가
            user_msg = Message(role="user", content=processed_message)
            self.conversation.add_message("user", processed_message)
            self.context_manager.add_to_context(user_msg)

            # 5. 컨텍스트 가져오기 (토큰 제한 적용)
            context_messages = self.context_manager.get_context(
                max_tokens=self.config.max_tokens
            )

            # 6. ChatMessage 형식으로 변환
            chat_messages = [
                ChatMessage(role=msg.role, text=msg.content)
                for msg in context_messages
            ]

            # 7. LLM 응답 생성 (도구 포함)
            logger.info(
                "응답 생성 시작",
                extra={
                    "context_length": len(chat_messages),
                    "tools_count": len(active_tools),
                },
            )

            if active_tools:
                response = await self.response_generator.generate_with_tools(
                    chat_messages, active_tools
                )
                self.metrics["tool_calls"] += 1
            else:
                response = await self.response_generator.generate(chat_messages)

            # 8. 응답을 컨텍스트에 추가
            assistant_msg = Message(role="assistant", content=response)
            self.conversation.add_message("assistant", response)
            self.context_manager.add_to_context(assistant_msg)

            # 9. 메트릭 업데이트
            elapsed_time = time.time() - start_time
            self._update_metrics(elapsed_time)

            logger.info(
                "대화 처리 완료",
                extra={
                    "response_length": len(response),
                    "elapsed_time": elapsed_time,
                    "total_messages": self.metrics["total_messages"],
                    "used_tools": len(active_tools) > 0,
                },
            )

            return response

        except Exception as e:
            logger.error(
                "대화 처리 실패",
                extra={"error": str(e), "elapsed_time": time.time() - start_time},
            )
            raise

    async def chat_stream(
        self, user_message: str, tools: list[Callable[..., Any]] | None = None
    ) -> AsyncIterator[str]:
        """스트리밍 방식으로 응답을 생성합니다.

        Args:
            user_message: 사용자 메시지
            tools: 이 대화에서만 사용할 도구 (None이면 Agent 레벨 도구 사용)

        Yields:
            응답 토큰

        Raises:
            ValueError: 메시지 검증 실패
            ResponseGenerationError: 응답 생성 실패

        Example:
            >>> async for token in agent.chat_stream("Tell me about AI"):
            ...     print(token, end="", flush=True)
        """
        start_time = time.time()
        active_tools = tools if tools is not None else self.tools

        try:
            # 1-4. 메시지 전처리 및 컨텍스트 추가 (chat과 동일)
            processed_message = self.message_processor.preprocess(user_message)
            self.message_processor.validate(processed_message)

            user_msg = Message(role="user", content=processed_message)
            self.conversation.add_message("user", processed_message)
            self.context_manager.add_to_context(user_msg)

            # 5. 컨텍스트 가져오기
            context_messages = self.context_manager.get_context(
                max_tokens=self.config.max_tokens
            )
            chat_messages = [
                ChatMessage(role=msg.role, text=msg.content)
                for msg in context_messages
            ]

            # 6. 스트리밍 응답 생성
            logger.info(
                "스트리밍 응답 생성 시작",
                extra={"tools_count": len(active_tools)},
            )
            full_response = ""

            # 도구 사용 시에는 일반 generate를 사용 (도구 호출 완료 후 스트리밍)
            if active_tools:
                response = await self.response_generator.generate_with_tools(
                    chat_messages, active_tools
                )
                self.metrics["tool_calls"] += 1
                
                # 완성된 응답을 토큰 단위로 분할하여 스트리밍 효과
                for i in range(0, len(response), 5):
                    chunk = response[i:i+5]
                    full_response += chunk
                    yield chunk
            else:
                async for token in self.response_generator.generate_stream(chat_messages):
                    full_response += token
                    yield token

            # 7. 완전한 응답을 컨텍스트에 추가
            assistant_msg = Message(role="assistant", content=full_response)
            self.conversation.add_message("assistant", full_response)
            self.context_manager.add_to_context(assistant_msg)

            # 8. 메트릭 업데이트
            elapsed_time = time.time() - start_time
            self._update_metrics(elapsed_time)

            logger.info(
                "스트리밍 대화 처리 완료",
                extra={
                    "response_length": len(full_response),
                    "elapsed_time": elapsed_time,
                    "used_tools": len(active_tools) > 0,
                },
            )

        except Exception as e:
            logger.error("스트리밍 대화 처리 실패", extra={"error": str(e)})
            raise

    def add_tool(self, tool: Callable[..., Any]) -> None:
        """도구를 Agent에 추가합니다.

        Args:
            tool: 추가할 도구 함수

        Example:
            >>> from src.agent.tools.web_search import search_web
            >>> agent.add_tool(search_web)
        """
        if tool not in self.tools:
            self.tools.append(tool)
            # ResponseGenerator는 재생성하지 않고 기존 인스턴스 유지
            # 도구는 generate_with_tools 호출 시 전달됨
            logger.info(f"도구 추가됨: {tool.__name__}")

    def remove_tool(self, tool: Callable[..., Any]) -> None:
        """도구를 Agent에서 제거합니다.

        Args:
            tool: 제거할 도구 함수

        Example:
            >>> agent.remove_tool(search_web)
        """
        if tool in self.tools:
            self.tools.remove(tool)
            # ResponseGenerator는 재생성하지 않고 기존 인스턴스 유지
            # 도구는 generate_with_tools 호출 시 전달됨
            logger.info(f"도구 제거됨: {tool.__name__}")

    def list_tools(self) -> list[str]:
        """현재 등록된 도구 목록을 반환합니다.

        Returns:
            도구 이름 리스트

        Example:
            >>> tools = agent.list_tools()
            >>> print(tools)
            ['search_web', 'calculate']
        """
        return [tool.__name__ for tool in self.tools]

    def reset_conversation(self) -> None:
        """대화를 초기화합니다.

        모든 메시지와 컨텍스트를 제거하고 메트릭을 리셋합니다.

        Example:
            >>> agent = ConversationAgent()
            >>> await agent.chat("안녕")
            >>> agent.reset_conversation()
            >>> agent.conversation.get_message_count()
            0
        """
        self.conversation.clear()
        self.context_manager.clear()
        self.metrics = {
            "total_messages": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
        }
        logger.info("대화 초기화 완료")

    def save_conversation(self, filepath: str | Path) -> None:
        """대화를 파일로 저장합니다.

        Args:
            filepath: 저장할 파일 경로

        Raises:
            IOError: 파일 저장 실패

        Example:
            >>> agent = ConversationAgent()
            >>> await agent.chat("안녕하세요")
            >>> agent.save_conversation("conversation.json")
        """
        filepath = Path(filepath)

        try:
            self.context_manager.save_to_file(filepath)
            logger.info("대화 저장 완료", extra={"filepath": str(filepath)})

        except Exception as e:
            logger.error("대화 저장 실패", extra={"error": str(e)})
            raise IOError(f"대화 저장 실패: {e}") from e

    def load_conversation(self, filepath: str | Path) -> None:
        """파일에서 대화를 로드합니다.

        Args:
            filepath: 로드할 파일 경로

        Raises:
            FileNotFoundError: 파일이 없음
            ValueError: 파일 형식 오류

        Example:
            >>> agent = ConversationAgent()
            >>> agent.load_conversation("conversation.json")
            >>> agent.conversation.get_message_count() > 0
            True
        """
        filepath = Path(filepath)

        try:
            self.context_manager.load_from_file(filepath)

            # Conversation 객체 재구성
            self.conversation = Conversation()
            for msg in self.context_manager.messages:
                self.conversation.add_message(msg.role, msg.content)

            logger.info("대화 로드 완료", extra={"filepath": str(filepath)})

        except Exception as e:
            logger.error("대화 로드 실패", extra={"error": str(e)})
            raise

    def get_metrics(self) -> dict[str, float | int]:
        """현재 성능 메트릭을 반환합니다.

        Returns:
            메트릭 딕셔너리

        Example:
            >>> metrics = agent.get_metrics()
            >>> metrics["tool_calls"]
            5
        """
        # 토큰 사용량 업데이트
        token_usage = self.response_generator.get_token_usage()
        self.metrics["total_tokens"] = token_usage["total_tokens"]

        return self.metrics.copy()

    def _update_metrics(self, elapsed_time: float) -> None:
        """메트릭을 업데이트합니다.

        Args:
            elapsed_time: 응답 생성에 소요된 시간 (초)
        """
        self.metrics["total_messages"] += 1
        self.metrics["total_response_time"] += elapsed_time
        self.metrics["average_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["total_messages"]
        )

    def get_conversation_summary(self) -> str:
        """현재 대화의 요약을 반환합니다.

        Returns:
            대화 요약 문자열

        Example:
            >>> agent = ConversationAgent()
            >>> summary = agent.get_conversation_summary()
            >>> isinstance(summary, str)
            True
        """
        message_count = len(self.conversation.messages)
        token_count = self.context_manager.get_total_tokens()

        return (
            f"대화 ID: {self.conversation.id}\n"
            f"메시지 수: {message_count}\n"
            f"토큰 수: {token_count}\n"
            f"평균 응답 시간: {self.metrics['average_response_time']:.2f}초"
        )
