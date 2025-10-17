"""메시지 전처리 및 검증을 담당하는 모듈."""

import html
import logging
import re
from typing import TypeAlias

logger = logging.getLogger(__name__)

IntentType: TypeAlias = str  # "question" | "command" | "conversation"


class MessageProcessor:
    """메시지를 전처리하고 검증하는 클래스.

    Attributes:
        max_length: 메시지 최대 길이
        min_length: 메시지 최소 길이
        forbidden_words: 금지어 목록

    Example:
        >>> processor = MessageProcessor(max_length=1000)
        >>> processed = processor.preprocess("  Hello   world!  ")
        >>> processed
        'Hello world!'
        >>> processor.validate(processed)
        True
    """

    def __init__(
        self,
        max_length: int = 4000,
        min_length: int = 1,
        forbidden_words: list[str] | None = None,
    ) -> None:
        """MessageProcessor를 초기화합니다.

        Args:
            max_length: 메시지 최대 길이 (기본값: 4000)
            min_length: 메시지 최소 길이 (기본값: 1)
            forbidden_words: 금지어 목록 (기본값: None)
        """
        self.max_length = max_length
        self.min_length = min_length
        self.forbidden_words = forbidden_words or []
        logger.info(
            "MessageProcessor 초기화",
            extra={
                "max_length": max_length,
                "min_length": min_length,
                "forbidden_words_count": len(self.forbidden_words),
            },
        )

    def preprocess(self, message: str) -> str:
        """메시지를 전처리합니다.

        Args:
            message: 전처리할 메시지

        Returns:
            전처리된 메시지

        Example:
            >>> processor = MessageProcessor()
            >>> processor.preprocess("  Hello   <script>alert('XSS')</script>  ")
            'Hello &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;'
        """
        # 1. 앞뒤 공백 제거
        processed = message.strip()

        # 2. 연속된 공백을 하나로
        processed = re.sub(r"\s+", " ", processed)

        # 3. 특수 문자 이스케이프 (XSS 방지)
        processed = html.escape(processed)

        # 4. 너무 긴 메시지는 truncate
        if len(processed) > self.max_length:
            processed = processed[: self.max_length]
            logger.warning(
                "메시지가 최대 길이를 초과하여 잘림",
                extra={
                    "original_length": len(message),
                    "truncated_length": self.max_length,
                },
            )

        return processed

    def validate(self, message: str) -> bool:
        """메시지를 검증합니다.

        Args:
            message: 검증할 메시지

        Returns:
            검증 통과 시 True

        Raises:
            ValueError: 메시지가 유효하지 않은 경우

        Example:
            >>> processor = MessageProcessor(min_length=1, max_length=100)
            >>> processor.validate("Hello")
            True
            >>> processor.validate("")
            Traceback (most recent call last):
                ...
            ValueError: 메시지는 비어있을 수 없습니다
        """
        # 1. 빈 메시지 체크
        if not message or not message.strip():
            raise ValueError("메시지는 비어있을 수 없습니다")

        # 2. 최소 길이 체크
        if len(message) < self.min_length:
            raise ValueError(
                f"메시지는 최소 {self.min_length}자 이상이어야 합니다 "
                f"(현재: {len(message)}자)"
            )

        # 3. 최대 길이 체크
        if len(message) > self.max_length:
            raise ValueError(
                f"메시지는 최대 {self.max_length}자를 초과할 수 없습니다 "
                f"(현재: {len(message)}자)"
            )

        # 4. 금지어 체크
        message_lower = message.lower()
        for word in self.forbidden_words:
            if word.lower() in message_lower:
                logger.warning(
                    "금지어 감지됨",
                    extra={"forbidden_word": word, "message_length": len(message)},
                )
                raise ValueError(f"금지어가 포함되어 있습니다: {word}")

        return True

    def extract_intent(self, message: str) -> dict[str, str | float]:
        """메시지에서 의도를 추출합니다.

        간단한 키워드 기반으로 질문/명령/대화를 분류합니다.

        Args:
            message: 의도를 추출할 메시지

        Returns:
            의도 정보를 담은 딕셔너리
            - intent: 의도 타입 ("question", "command", "conversation")
            - confidence: 신뢰도 점수 (0.0 ~ 1.0)

        Example:
            >>> processor = MessageProcessor()
            >>> result = processor.extract_intent("날씨가 어때?")
            >>> result["intent"]
            'question'
            >>> result["confidence"] > 0.5
            True
        """
        message_lower = message.lower()

        # 질문 패턴
        question_patterns = [
            r"[?？]$",  # 물음표로 끝남
            r"^(what|when|where|who|why|how|어떻|무엇|언제|어디|누가|왜)",
            r"(알려|설명|가르쳐|궁금)",
        ]

        # 명령 패턴
        command_patterns = [
            r"^(해줘|해|실행|시작|종료|만들어|생성|삭제)",
            r"(please|할게|하자)",
        ]

        # 질문 체크
        question_score = sum(
            1 for pattern in question_patterns if re.search(pattern, message_lower)
        )
        if question_score > 0:
            confidence = min(question_score * 0.4, 1.0)
            return {"intent": "question", "confidence": confidence}

        # 명령 체크
        command_score = sum(
            1 for pattern in command_patterns if re.search(pattern, message_lower)
        )
        if command_score > 0:
            confidence = min(command_score * 0.4, 1.0)
            return {"intent": "command", "confidence": confidence}

        # 기본값: 대화
        return {"intent": "conversation", "confidence": 0.5}
