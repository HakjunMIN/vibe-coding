"""대화 컨텍스트를 관리하는 모듈."""

import json
import logging
import threading
from pathlib import Path

import tiktoken

from .models import Message

logger = logging.getLogger(__name__)


class ContextManager:
    """대화 컨텍스트를 관리하는 클래스.

    토큰 제한 내에서 메시지를 관리하고, 오래된 대화를 요약하며,
    파일 시스템에 저장/로드하는 기능을 제공합니다.

    Attributes:
        messages: 컨텍스트에 포함된 메시지 리스트
        max_messages: 최대 메시지 개수
        model_name: 토큰 계산에 사용할 모델명
        lock: 스레드 안전성을 위한 락

    Example:
        >>> manager = ContextManager(max_messages=10)
        >>> manager.add_to_context(Message(role="user", content="안녕하세요"))
        >>> context = manager.get_context(max_tokens=4000)
        >>> len(context) <= 10
        True
    """

    def __init__(
        self,
        max_messages: int = 10,
        model_name: str = "gpt-4",
    ) -> None:
        """ContextManager를 초기화합니다.

        Args:
            max_messages: 컨텍스트에 유지할 최대 메시지 개수
            model_name: 토큰 계산에 사용할 모델명
        """
        self.messages: list[Message] = []
        self.max_messages = max_messages
        self.model_name = model_name
        self.lock = threading.Lock()

        # tiktoken 인코더 초기화
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(
                f"모델 '{model_name}'에 대한 인코더를 찾을 수 없습니다. cl100k_base 사용",
            )
            self.encoder = tiktoken.get_encoding("cl100k_base")

        logger.info(
            "ContextManager 초기화",
            extra={"max_messages": max_messages, "model": model_name},
        )

    def _count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수를 계산합니다.

        Args:
            text: 토큰 수를 계산할 텍스트

        Returns:
            토큰 수
        """
        return len(self.encoder.encode(text))

    def _count_message_tokens(self, message: Message) -> int:
        """메시지의 토큰 수를 계산합니다.

        Args:
            message: 토큰 수를 계산할 메시지

        Returns:
            토큰 수 (role, content 포함)
        """
        # role과 content에 대한 토큰 수 + 메시지 오버헤드 (약 4 토큰)
        tokens = self._count_tokens(message.role)
        tokens += self._count_tokens(message.content)
        tokens += 4  # 메시지 구조 오버헤드
        return tokens

    def add_to_context(self, message: Message) -> None:
        """메시지를 컨텍스트에 추가합니다.

        윈도우 크기 제한을 초과하면 가장 오래된 메시지를 제거합니다.
        단, system 메시지는 항상 유지됩니다.

        Args:
            message: 추가할 메시지

        Example:
            >>> manager = ContextManager(max_messages=2)
            >>> manager.add_to_context(Message(role="user", content="첫 메시지"))
            >>> manager.add_to_context(Message(role="assistant", content="응답"))
            >>> manager.add_to_context(Message(role="user", content="세 번째"))
            >>> len(manager.messages)
            2
        """
        with self.lock:
            self.messages.append(message)

            # 윈도우 크기 제한 확인 (system 메시지 제외)
            non_system_messages = [
                msg for msg in self.messages if msg.role != "system"
            ]

            if len(non_system_messages) > self.max_messages:
                # 오래된 non-system 메시지 제거
                for i, msg in enumerate(self.messages):
                    if msg.role != "system":
                        self.messages.pop(i)
                        logger.info(
                            "윈도우 크기 초과로 메시지 제거",
                            extra={"removed_role": msg.role},
                        )
                        break

            logger.debug(
                "메시지 추가됨",
                extra={
                    "role": message.role,
                    "content_length": len(message.content),
                    "total_messages": len(self.messages),
                },
            )

    def get_context(self, max_tokens: int = 4000) -> list[Message]:
        """토큰 제한 내에서 컨텍스트를 반환합니다.

        토큰 제한을 초과하면 오래된 메시지부터 제거합니다.
        system 메시지는 항상 유지됩니다.

        Args:
            max_tokens: 최대 토큰 수

        Returns:
            토큰 제한 내의 메시지 리스트

        Example:
            >>> manager = ContextManager()
            >>> manager.add_to_context(Message(role="user", content="안녕"))
            >>> context = manager.get_context(max_tokens=100)
            >>> len(context) >= 1
            True
        """
        with self.lock:
            if not self.messages:
                return []

            # system 메시지와 일반 메시지 분리
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]

            # system 메시지 토큰 계산
            total_tokens = sum(
                self._count_message_tokens(msg) for msg in system_messages
            )

            # 최근 메시지부터 추가
            result_messages = system_messages.copy()
            for message in reversed(other_messages):
                message_tokens = self._count_message_tokens(message)

                if total_tokens + message_tokens <= max_tokens:
                    result_messages.append(message)
                    total_tokens += message_tokens
                else:
                    logger.info(
                        "토큰 제한 도달",
                        extra={
                            "total_tokens": total_tokens,
                            "max_tokens": max_tokens,
                            "messages_included": len(result_messages),
                        },
                    )
                    break

            # 원래 순서로 정렬 (system 메시지 먼저, 그 다음 시간순)
            result_messages.sort(
                key=lambda msg: (
                    msg.role != "system",
                    msg.timestamp,
                )
            )

            return result_messages

    def summarize_old_context(self, summarizer_func: callable) -> str:
        """오래된 대화를 요약합니다.

        Args:
            summarizer_func: 요약을 생성하는 함수 (messages -> str)

        Returns:
            생성된 요약 텍스트

        Raises:
            ValueError: 요약할 메시지가 없는 경우

        Example:
            >>> async def summarize(messages):
            ...     return "대화 요약"
            >>> manager = ContextManager()
            >>> manager.add_to_context(Message(role="user", content="안녕"))
            >>> summary = manager.summarize_old_context(summarize)
        """
        with self.lock:
            if len(self.messages) < 2:
                raise ValueError("요약할 메시지가 충분하지 않습니다")

            # system 메시지를 제외한 메시지들
            messages_to_summarize = [
                msg for msg in self.messages if msg.role != "system"
            ]

            if not messages_to_summarize:
                raise ValueError("요약할 메시지가 없습니다")

            logger.info(
                "대화 요약 시작", extra={"message_count": len(messages_to_summarize)}
            )

            # 요약 생성
            summary = summarizer_func(messages_to_summarize)

            # 요약을 system 메시지로 추가
            summary_message = Message(
                role="system",
                content=f"이전 대화 요약: {summary}",
            )

            # 요약된 메시지들 제거하고 요약본 추가
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            self.messages = system_messages + [summary_message]

            logger.info(
                "대화 요약 완료",
                extra={"summary_length": len(summary), "messages_removed": len(messages_to_summarize)},
            )

            return summary

    def save_to_file(self, filepath: str | Path) -> None:
        """대화 기록을 JSON 파일로 저장합니다.

        Args:
            filepath: 저장할 파일 경로

        Raises:
            IOError: 파일 저장 실패 시

        Example:
            >>> manager = ContextManager()
            >>> manager.add_to_context(Message(role="user", content="안녕"))
            >>> manager.save_to_file("conversation.json")
        """
        filepath = Path(filepath)

        with self.lock:
            data = {
                "model_name": self.model_name,
                "max_messages": self.max_messages,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata,
                    }
                    for msg in self.messages
                ],
            }

            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with filepath.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                logger.info(
                    "대화 기록 저장됨",
                    extra={"filepath": str(filepath), "message_count": len(self.messages)},
                )

            except Exception as e:
                logger.error("대화 기록 저장 실패", extra={"error": str(e)})
                raise IOError(f"파일 저장 실패: {e}") from e

    def load_from_file(self, filepath: str | Path) -> None:
        """JSON 파일에서 대화 기록을 로드합니다.

        Args:
            filepath: 로드할 파일 경로

        Raises:
            FileNotFoundError: 파일이 없는 경우
            ValueError: 파일 형식이 올바르지 않은 경우

        Example:
            >>> manager = ContextManager()
            >>> manager.load_from_file("conversation.json")
            >>> len(manager.messages) > 0
            True
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

        with self.lock:
            try:
                with filepath.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                self.model_name = data.get("model_name", self.model_name)
                self.max_messages = data.get("max_messages", self.max_messages)

                self.messages = [
                    Message(
                        role=msg["role"],
                        content=msg["content"],
                        metadata=msg.get("metadata"),
                    )
                    for msg in data["messages"]
                ]

                logger.info(
                    "대화 기록 로드됨",
                    extra={"filepath": str(filepath), "message_count": len(self.messages)},
                )

            except (json.JSONDecodeError, KeyError) as e:
                logger.error("대화 기록 로드 실패", extra={"error": str(e)})
                raise ValueError(f"잘못된 파일 형식: {e}") from e

    def clear(self) -> None:
        """컨텍스트를 초기화합니다.

        Example:
            >>> manager = ContextManager()
            >>> manager.add_to_context(Message(role="user", content="안녕"))
            >>> manager.clear()
            >>> len(manager.messages)
            0
        """
        with self.lock:
            self.messages.clear()
            logger.info("컨텍스트 초기화됨")

    def get_message_count(self) -> int:
        """현재 컨텍스트의 메시지 개수를 반환합니다.

        Returns:
            메시지 개수

        Example:
            >>> manager = ContextManager()
            >>> manager.get_message_count()
            0
        """
        with self.lock:
            return len(self.messages)

    def get_total_tokens(self) -> int:
        """현재 컨텍스트의 총 토큰 수를 반환합니다.

        Returns:
            총 토큰 수

        Example:
            >>> manager = ContextManager()
            >>> manager.add_to_context(Message(role="user", content="안녕"))
            >>> manager.get_total_tokens() > 0
            True
        """
        with self.lock:
            return sum(self._count_message_tokens(msg) for msg in self.messages)
