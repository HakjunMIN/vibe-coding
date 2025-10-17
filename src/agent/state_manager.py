"""Agent 상태 관리 시스템."""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .models import Conversation
from .storage.base import NotFoundError, StorageBackend, StorageError

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Agent 세션의 상태를 표현하는 모델.

    Attributes:
        session_id: 세션의 고유 식별자
        user_id: 사용자 ID (선택적)
        conversation: 대화 객체
        user_preferences: 사용자 설정
        plugin_data: 플러그인별 데이터
        created_at: 세션 생성 시간
        updated_at: 세션 마지막 업데이트 시간
        expires_at: 세션 만료 시간 (TTL)

    Example:
        >>> state = AgentState(
        ...     session_id="session_123",
        ...     user_id="user_456",
        ...     conversation=Conversation()
        ... )
        >>> state.session_id
        'session_123'
    """

    session_id: str
    user_id: str | None = None
    conversation: Conversation = Field(default_factory=Conversation)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    plugin_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """세션이 만료되었는지 확인합니다.

        Returns:
            만료 여부

        Example:
            >>> state.is_expired()
            False
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def extend_expiry(self, hours: int = 24) -> None:
        """세션 만료 시간을 연장합니다.

        Args:
            hours: 연장할 시간 (시간 단위)

        Example:
            >>> state.extend_expiry(48)  # 48시간 연장
        """
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """모델을 딕셔너리로 변환합니다.

        Returns:
            딕셔너리 형태의 상태 데이터

        Example:
            >>> data = state.to_dict()
            >>> data["session_id"]
            'session_123'
        """
        data = self.model_dump()
        
        # Conversation 객체를 딕셔너리로 변환 (UUID와 datetime 처리)
        conversation_data = self.conversation.model_dump()
        # UUID를 문자열로 변환
        if "id" in conversation_data:
            conversation_data["id"] = str(conversation_data["id"])
        # Conversation의 datetime 필드들을 ISO 문자열로 변환
        for key in ["created_at", "updated_at"]:
            if key in conversation_data and conversation_data[key] is not None:
                conversation_data[key] = conversation_data[key].isoformat()
        
        # Message의 timestamp도 처리
        if "messages" in conversation_data:
            for message in conversation_data["messages"]:
                if "timestamp" in message and message["timestamp"] is not None:
                    message["timestamp"] = message["timestamp"].isoformat()
        
        data["conversation"] = conversation_data
        
        # AgentState의 datetime 객체를 ISO 문자열로 변환
        for key in ["created_at", "updated_at", "expires_at"]:
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        """딕셔너리에서 모델을 생성합니다.

        Args:
            data: 딕셔너리 형태의 상태 데이터

        Returns:
            AgentState 인스턴스

        Example:
            >>> data = {"session_id": "session_123", ...}
            >>> state = AgentState.from_dict(data)
        """
        # Conversation 객체 재구성
        if "conversation" in data and isinstance(data["conversation"], dict):
            conversation_data = data["conversation"].copy()
            
            # UUID 문자열을 UUID 객체로 변환
            if "id" in conversation_data and isinstance(conversation_data["id"], str):
                from uuid import UUID
                conversation_data["id"] = UUID(conversation_data["id"])
            
            # Conversation의 datetime 문자열을 객체로 변환
            for key in ["created_at", "updated_at"]:
                if key in conversation_data and conversation_data[key] is not None:
                    if isinstance(conversation_data[key], str):
                        conversation_data[key] = datetime.fromisoformat(conversation_data[key])
            
            # Message의 timestamp도 처리
            if "messages" in conversation_data:
                for message in conversation_data["messages"]:
                    if "timestamp" in message and message["timestamp"] is not None:
                        if isinstance(message["timestamp"], str):
                            message["timestamp"] = datetime.fromisoformat(message["timestamp"])
            
            data["conversation"] = Conversation(**conversation_data)

        # AgentState의 datetime 문자열을 객체로 변환
        for key in ["created_at", "updated_at", "expires_at"]:
            if key in data and data[key] is not None:
                if isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key])

        return cls(**data)


class JSONStorage(StorageBackend):
    """JSON 파일 기반 저장소 구현."""

    def __init__(self, storage_dir: str | Path = "data/sessions") -> None:
        """JSONStorage를 초기화합니다.

        Args:
            storage_dir: 저장소 디렉토리 경로
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """키에 해당하는 파일 경로를 반환합니다."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{safe_key}.json"

    def save(self, key: str, value: dict[str, Any]) -> None:
        """키-값 쌍을 JSON 파일로 저장합니다."""
        try:
            file_path = self._get_file_path(key)
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise StorageError(f"저장 실패: {e}") from e

    def load(self, key: str) -> dict[str, Any]:
        """JSON 파일에서 값을 로드합니다."""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            raise NotFoundError(f"키를 찾을 수 없습니다: {key}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"로드 실패: {e}") from e

    def delete(self, key: str) -> None:
        """파일을 삭제합니다."""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            raise NotFoundError(f"키를 찾을 수 없습니다: {key}")

        try:
            file_path.unlink()
        except Exception as e:
            raise StorageError(f"삭제 실패: {e}") from e

    def exists(self, key: str) -> bool:
        """파일이 존재하는지 확인합니다."""
        return self._get_file_path(key).exists()

    def list_keys(self, pattern: str = "*") -> list[str]:
        """패턴에 매칭되는 키 목록을 반환합니다."""
        try:
            if pattern == "*":
                pattern = "*.json"
            elif not pattern.endswith(".json"):
                pattern = pattern.replace("*", "*.json")

            files = list(self.storage_dir.glob(pattern))
            return [f.stem for f in files if f.is_file()]
        except Exception as e:
            raise StorageError(f"키 목록 조회 실패: {e}") from e

    # 비동기 메서드들 (동기 메서드를 래핑)
    async def save_async(self, key: str, value: dict[str, Any]) -> None:
        """비동기적으로 저장합니다."""
        await asyncio.get_event_loop().run_in_executor(None, self.save, key, value)

    async def load_async(self, key: str) -> dict[str, Any]:
        """비동기적으로 로드합니다."""
        return await asyncio.get_event_loop().run_in_executor(None, self.load, key)

    async def delete_async(self, key: str) -> None:
        """비동기적으로 삭제합니다."""
        await asyncio.get_event_loop().run_in_executor(None, self.delete, key)

    async def exists_async(self, key: str) -> bool:
        """비동기적으로 존재 여부를 확인합니다."""
        return await asyncio.get_event_loop().run_in_executor(None, self.exists, key)

    async def list_keys_async(self, pattern: str = "*") -> list[str]:
        """비동기적으로 키 목록을 반환합니다."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.list_keys, pattern
        )


class StateManager:
    """Agent 상태를 관리하는 매니저 클래스.

    세션 생성, 조회, 업데이트, 삭제 및 만료 관리를 담당합니다.
    스레드 안전성과 자동 저장 기능을 제공합니다.

    Attributes:
        storage: 저장소 백엔드
        sessions: 메모리 내 세션 캐시
        auto_save_enabled: 자동 저장 활성화 여부
        default_ttl_hours: 기본 세션 TTL (시간)
        lock: 스레드 안전성을 위한 락

    Example:
        >>> manager = StateManager()
        >>> session_id = manager.create_session("user_123")
        >>> state = manager.get_session(session_id)
        >>> state.user_id
        'user_123'
    """

    def __init__(
        self,
        storage: StorageBackend | None = None,
        auto_save_interval: int = 300,  # 5분
        default_ttl_hours: int = 24,
    ) -> None:
        """StateManager를 초기화합니다.

        Args:
            storage: 저장소 백엔드 (None이면 JSONStorage 사용)
            auto_save_interval: 자동 저장 간격 (초)
            default_ttl_hours: 기본 세션 TTL (시간)
        """
        self.storage = storage or JSONStorage()
        self.sessions: dict[str, AgentState] = {}
        self.auto_save_enabled = True
        self.auto_save_interval = auto_save_interval
        self.default_ttl_hours = default_ttl_hours
        self.lock = threading.RLock()

        # 기존 세션 로드
        self._load_existing_sessions()

        # 자동 저장 스레드 시작
        if self.auto_save_enabled:
            self._start_auto_save_thread()

        logger.info(
            "StateManager 초기화 완료",
            extra={
                "storage_type": type(self.storage).__name__,
                "loaded_sessions": len(self.sessions),
                "auto_save_interval": auto_save_interval,
            },
        )

    def create_session(self, user_id: str | None = None) -> str:
        """새 세션을 생성합니다.

        Args:
            user_id: 사용자 ID (선택적)

        Returns:
            생성된 세션 ID

        Example:
            >>> session_id = manager.create_session("user_123")
            >>> len(session_id) > 0
            True
        """
        with self.lock:
            session_id = str(uuid4())
            expires_at = datetime.now() + timedelta(hours=self.default_ttl_hours)

            state = AgentState(
                session_id=session_id,
                user_id=user_id,
                expires_at=expires_at,
            )

            self.sessions[session_id] = state

            # 즉시 저장
            try:
                self.storage.save(session_id, state.to_dict())
            except Exception as e:
                logger.error(f"세션 저장 실패: {session_id} - {e}")

            logger.info(
                f"새 세션 생성: {session_id}",
                extra={"session_id": session_id, "user_id": user_id},
            )

            return session_id

    def get_session(self, session_id: str) -> AgentState:
        """세션을 조회합니다.

        Args:
            session_id: 조회할 세션 ID

        Returns:
            AgentState 객체

        Raises:
            NotFoundError: 세션을 찾을 수 없는 경우

        Example:
            >>> state = manager.get_session("session_123")
            >>> state.session_id
            'session_123'
        """
        with self.lock:
            # 메모리에서 먼저 확인
            if session_id in self.sessions:
                state = self.sessions[session_id]
                if state.is_expired():
                    self.delete_session(session_id)
                    raise NotFoundError(f"세션이 만료됨: {session_id}")
                return state

            # 저장소에서 로드 시도
            try:
                data = self.storage.load(session_id)
                state = AgentState.from_dict(data)

                if state.is_expired():
                    self.delete_session(session_id)
                    raise NotFoundError(f"세션이 만료됨: {session_id}")

                # 메모리에 캐시
                self.sessions[session_id] = state
                return state

            except NotFoundError:
                raise NotFoundError(f"세션을 찾을 수 없습니다: {session_id}")

    def update_session(self, session_id: str, state: AgentState) -> None:
        """세션을 업데이트합니다.

        Args:
            session_id: 업데이트할 세션 ID
            state: 새로운 상태

        Raises:
            NotFoundError: 세션을 찾을 수 없는 경우

        Example:
            >>> state = manager.get_session("session_123")
            >>> state.user_preferences["theme"] = "dark"
            >>> manager.update_session("session_123", state)
        """
        with self.lock:
            if session_id not in self.sessions:
                # 세션이 메모리에 없으면 존재 여부 확인
                if not self.storage.exists(session_id):
                    raise NotFoundError(f"세션을 찾을 수 없습니다: {session_id}")

            # 업데이트 시간 갱신
            state.updated_at = datetime.now()
            state.session_id = session_id  # 세션 ID 보장

            # 메모리와 저장소 모두 업데이트
            self.sessions[session_id] = state

            try:
                self.storage.save(session_id, state.to_dict())
            except Exception as e:
                logger.error(f"세션 업데이트 저장 실패: {session_id} - {e}")

            logger.debug(f"세션 업데이트: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 삭제할 세션 ID

        Raises:
            NotFoundError: 세션을 찾을 수 없는 경우

        Example:
            >>> manager.delete_session("session_123")
        """
        with self.lock:
            # 메모리에서 제거
            if session_id in self.sessions:
                del self.sessions[session_id]

            # 저장소에서 제거
            try:
                self.storage.delete(session_id)
                logger.info(f"세션 삭제: {session_id}")
            except NotFoundError:
                if session_id not in self.sessions:
                    raise NotFoundError(f"세션을 찾을 수 없습니다: {session_id}")

    def list_sessions(self, user_id: str | None = None) -> list[str]:
        """세션 목록을 반환합니다.

        Args:
            user_id: 특정 사용자의 세션만 조회 (None이면 전체)

        Returns:
            세션 ID 리스트

        Example:
            >>> sessions = manager.list_sessions("user_123")
            >>> len(sessions) >= 0
            True
        """
        with self.lock:
            if user_id is None:
                return list(self.sessions.keys())

            return [
                session_id
                for session_id, state in self.sessions.items()
                if state.user_id == user_id
            ]

    def cleanup_expired_sessions(self) -> int:
        """만료된 세션들을 정리합니다.

        Returns:
            정리된 세션 개수

        Example:
            >>> cleaned = manager.cleanup_expired_sessions()
            >>> cleaned >= 0
            True
        """
        with self.lock:
            expired_sessions = []

            for session_id, state in self.sessions.items():
                if state.is_expired():
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                try:
                    self.delete_session(session_id)
                except Exception as e:
                    logger.error(f"만료된 세션 삭제 실패: {session_id} - {e}")

            if expired_sessions:
                logger.info(f"만료된 세션 정리 완료: {len(expired_sessions)}개")

            return len(expired_sessions)

    def _load_existing_sessions(self) -> None:
        """저장소에서 기존 세션들을 로드합니다."""
        try:
            session_keys = self.storage.list_keys("*")
            loaded_count = 0

            for session_id in session_keys:
                try:
                    data = self.storage.load(session_id)
                    state = AgentState.from_dict(data)

                    if not state.is_expired():
                        self.sessions[session_id] = state
                        loaded_count += 1
                    else:
                        # 만료된 세션은 삭제
                        self.storage.delete(session_id)

                except Exception as e:
                    logger.warning(f"세션 로드 실패: {session_id} - {e}")

            logger.info(f"기존 세션 로드 완료: {loaded_count}개")

        except Exception as e:
            logger.error(f"세션 로드 실패: {e}")

    def _start_auto_save_thread(self) -> None:
        """자동 저장 스레드를 시작합니다."""

        def auto_save_worker():
            while self.auto_save_enabled:
                try:
                    time.sleep(self.auto_save_interval)
                    self._auto_save()
                except Exception as e:
                    logger.error(f"자동 저장 실패: {e}")

        thread = threading.Thread(target=auto_save_worker, daemon=True)
        thread.start()
        logger.info("자동 저장 스레드 시작")

    def _auto_save(self) -> None:
        """모든 세션을 자동으로 저장합니다."""
        with self.lock:
            saved_count = 0
            for session_id, state in self.sessions.items():
                try:
                    self.storage.save(session_id, state.to_dict())
                    saved_count += 1
                except Exception as e:
                    logger.error(f"자동 저장 실패: {session_id} - {e}")

            # 만료된 세션 정리
            self.cleanup_expired_sessions()

            logger.debug(f"자동 저장 완료: {saved_count}개 세션")

    def stop(self) -> None:
        """StateManager를 정지합니다.

        자동 저장을 중단하고 마지막으로 모든 세션을 저장합니다.

        Example:
            >>> manager.stop()
        """
        self.auto_save_enabled = False
        self._auto_save()
        logger.info("StateManager 정지")
