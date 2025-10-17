"""대화 메시지를 위한 Pydantic 모델."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """대화 메시지를 표현하는 모델.

    Attributes:
        role: 메시지 역할 ("user", "assistant", "system" 중 하나)
        content: 메시지 내용
        timestamp: 메시지 생성 시간 (자동 생성)
        metadata: 추가 메타데이터 (선택적)

    Example:
        >>> message = Message(role="user", content="안녕하세요")
        >>> message.role
        'user'
        >>> message.timestamp  # 자동으로 현재 시간 설정됨
        datetime.datetime(...)
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, str] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """메시지 내용을 검증합니다.

        Args:
            v: 검증할 메시지 내용

        Returns:
            검증된 메시지 내용

        Raises:
            ValueError: 메시지가 비어있는 경우
        """
        if not v or not v.strip():
            raise ValueError("메시지 내용은 비어있을 수 없습니다")
        return v.strip()


class Conversation(BaseModel):
    """대화를 관리하는 모델.

    Attributes:
        id: 대화의 고유 식별자 (UUID)
        messages: 메시지 리스트
        created_at: 대화 생성 시간
        updated_at: 대화 수정 시간

    Example:
        >>> conversation = Conversation()
        >>> conversation.add_message("user", "안녕하세요")
        >>> conversation.add_message("assistant", "안녕하세요! 무엇을 도와드릴까요?")
        >>> len(conversation.messages)
        2
        >>> history = conversation.get_history(limit=1)
        >>> len(history)
        1
    """

    id: UUID = Field(default_factory=uuid4)
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_message(
        self, role: Literal["user", "assistant", "system"], content: str
    ) -> None:
        """대화에 새 메시지를 추가합니다.

        Args:
            role: 메시지 역할
            content: 메시지 내용

        Raises:
            ValueError: 메시지 검증에 실패한 경우

        Example:
            >>> conversation = Conversation()
            >>> conversation.add_message("user", "안녕하세요")
            >>> conversation.messages[-1].role
            'user'
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, limit: int | None = None) -> list[Message]:
        """최근 메시지 기록을 반환합니다.

        Args:
            limit: 반환할 메시지 개수 (None이면 전체)

        Returns:
            메시지 리스트 (최신순)

        Example:
            >>> conversation = Conversation()
            >>> conversation.add_message("user", "첫 메시지")
            >>> conversation.add_message("user", "두 번째 메시지")
            >>> history = conversation.get_history(limit=1)
            >>> history[0].content
            '두 번째 메시지'
        """
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit > 0 else []

    def clear(self) -> None:
        """대화를 초기화합니다.

        모든 메시지를 제거하고 updated_at을 갱신합니다.

        Example:
            >>> conversation = Conversation()
            >>> conversation.add_message("user", "테스트")
            >>> conversation.clear()
            >>> len(conversation.messages)
            0
        """
        self.messages.clear()
        self.updated_at = datetime.now()
