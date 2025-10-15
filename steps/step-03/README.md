# Step 03: 메시지 처리 및 응답 생성

## 🎯 학습 목표

이 단계에서는 Agent가 사용자 메시지를 받아 처리하고, LLM을 통해 응답을 생성하는 핵심 기능을 구현합니다. 대화 컨텍스트 관리와 메모리 기능도 추가합니다.

## 📝 이 단계에서 배울 내용

- 메시지 처리 파이프라인 구현 프롬프트
- LLM 통합 및 응답 생성 요청
- 대화 컨텍스트 관리 프롬프트
- 스트리밍 응답 처리 방법

## 🚀 시작하기

### 1단계: 메시지 모델 정의

#### 📌 목표
대화 메시지를 표현하는 데이터 모델을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/models.py` 생성 후 Copilot Chat:**

```
대화 메시지를 위한 Pydantic 모델을 만들어줘.

필요한 모델:
1. Message:
   - role: "user" | "assistant" | "system"
   - content: 메시지 내용
   - timestamp: 생성 시간 (자동 생성)
   - metadata: 추가 메타데이터 (선택, dict)

2. Conversation:
   - id: 대화 ID (UUID)
   - messages: Message 리스트
   - created_at: 생성 시간
   - updated_at: 수정 시간
   - add_message(role, content): 메시지 추가 메서드
   - get_history(limit): 최근 N개 메시지 반환
   - clear(): 대화 초기화

모든 필드에 타입 힌트와 검증 로직 포함.
timestamp는 datetime 객체로, 자동으로 현재 시간 설정.
Google 스타일 docstring 추가.
```

#### 💡 프롬프트 작성 팁

- **데이터 구조 명확히**: 필드명, 타입, 관계 설명
- **자동 생성 필드 명시**: timestamp, UUID 등
- **메서드 시그니처 제공**: 파라미터와 반환 타입
- **검증 규칙 포함**: role의 가능한 값 등

### 2단계: 메시지 프로세서 구현

#### 📌 목표
메시지를 전처리하고 검증하는 프로세서를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/message_processor.py` 생성 후:**

```
메시지를 전처리하고 검증하는 MessageProcessor 클래스를 만들어줘.

요구사항:
- 클래스명: MessageProcessor
- 메서드:
  1. preprocess(message: str) -> str:
     - 앞뒤 공백 제거
     - 연속된 공백을 하나로
     - 특수 문자 이스케이프 (보안)
     - 너무 긴 메시지는 truncate
     
  2. validate(message: str) -> bool:
     - 빈 메시지 체크
     - 최소/최대 길이 체크
     - 금지어 체크 (설정 가능)
     - 유효하지 않으면 ValueError
     
  3. extract_intent(message: str) -> dict:
     - 메시지에서 의도 추출 (간단한 키워드 기반)
     - 질문/명령/대화 등 분류
     - 신뢰도 점수 포함

- __init__에서 설정 받기 (max_length, forbidden_words 등)
- 각 메서드는 순수 함수로 작성 (사이드 이펙트 없이)
- 로깅 추가
- 타입 힌트와 docstring 포함
```

#### 📋 심화 프롬프트

더 고급 기능이 필요하다면:

```
MessageProcessor에 다음 기능을 추가해줘:

1. detect_language(message: str) -> str:
   - 메시지의 언어 감지 (한국어/영어)
   - langdetect 라이브러리 사용
   
2. anonymize_pii(message: str) -> str:
   - 개인정보 마스킹 (이메일, 전화번호 등)
   - 정규표현식으로 패턴 매칭
   
3. add_context(message: str, context: dict) -> str:
   - 메시지에 컨텍스트 정보 추가
   - 템플릿 형식으로 조합

각 기능은 개별 메서드로 구현하고, preprocess에서 조합해서 사용할 수 있게 해줘.
```

### 3단계: 응답 생성기 구현

#### 📌 목표
LLM을 호출하고 응답을 생성하는 클래스를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/response_generator.py` 생성 후:**

```
LLM 응답 생성을 담당하는 ResponseGenerator 클래스를 만들어줘.

Microsoft Agent Framework 패턴 참고:
- https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents

요구사항:
- agent_framework의 ChatAgent와 Chat Client 활용
- __init__에서 AgentConfig 받기
- 메서드:
  1. async generate(messages: list[ChatMessage]) -> str:
     - ChatMessage 리스트를 사용
     - ChatAgent.run() 호출
     - 응답 추출 및 반환
     - 에러 처리 (API 실패, 타임아웃 등)
     
  2. async generate_stream(messages: list[ChatMessage]) -> AsyncIterator[str]:
     - 스트리밍 응답 생성
     - ChatAgent.run_stream() 사용
     - async for로 토큰 단위 반환
     
  3. async generate_with_tools(messages: list[ChatMessage], tools: list) -> str:
     - Tool/Function calling 지원
     - ChatAgent에 tools 전달
     - 도구 실행 결과 자동 처리

- 재시도 로직 포함 (exponential backoff)
- 토큰 사용량 추적
- 응답 캐싱 (같은 메시지는 캐시 사용)
- 타입 힌트와 docstring
- async/await 패턴 사용

agent_framework.openai의 OpenAIChatClient나 
agent_framework.azure의 AzureOpenAIChatClient를 활용해줘.
공식 샘플의 패턴을 따라서 구현해줘.
```

#### 💡 프롬프트 작성 팁

- **API 통합 명시**: 사용할 라이브러리나 API
- **비동기 처리 고려**: async/await 필요 여부
- **최적화 요구**: 캐싱, 재시도 등
- **모니터링 요소**: 토큰 사용량, 응답 시간 등

### 4단계: 대화 컨텍스트 매니저

#### 📌 목표
대화의 컨텍스트를 관리하고 메모리 기능을 구현합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/context_manager.py` 생성 후:**

```
대화 컨텍스트를 관리하는 ContextManager 클래스를 만들어줘.

요구사항:
- 클래스명: ContextManager
- 메서드:
  1. add_to_context(message: Message):
     - 메시지를 컨텍스트에 추가
     - 윈도우 크기 제한 (예: 최근 10개만)
     
  2. get_context(max_tokens: int = 4000) -> list[Message]:
     - 토큰 제한 내에서 최대한 많은 메시지 반환
     - 오래된 메시지부터 제거
     - 항상 system message는 유지
     
  3. summarize_old_context() -> str:
     - 오래된 대화를 요약
     - LLM을 사용해서 요약 생성
     - 요약본을 컨텍스트에 추가
     
  4. save_to_file(filepath: str):
     - 대화 기록을 JSON 파일로 저장
     
  5. load_from_file(filepath: str):
     - JSON 파일에서 대화 기록 로드

- 토큰 카운팅 함수 포함 (tiktoken 사용)
- 메모리 효율적으로 관리
- 스레드 세이프하게 구현
- 타입 힌트와 docstring
```

#### 📋 추가 기능 프롬프트

```
ContextManager에 다음 고급 기능을 추가해줘:

1. search_context(query: str) -> list[Message]:
   - 컨텍스트에서 키워드 검색
   - 유사도 기반 검색 (임베딩 사용)
   
2. extract_entities(messages: list[Message]) -> dict:
   - 대화에서 언급된 엔티티 추출
   - 인명, 장소, 날짜 등
   
3. get_summary() -> str:
   - 전체 대화의 요약 반환
   - 주요 토픽과 결론 포함

각 기능은 선택적으로 활성화할 수 있게 설정으로 제어해줘.
```

### 5단계: ConversationAgent 통합 클래스

#### 📌 목표
모든 컴포넌트를 통합하는 고수준 Agent 클래스를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/conversation_agent.py` 생성 후:**

```
모든 컴포넌트를 통합하는 ConversationAgent 클래스를 만들어줘.

요구사항:
- BaseAgent 상속
- 컴포넌트 조합:
  - MessageProcessor: 메시지 전처리
  - ResponseGenerator: 응답 생성
  - ContextManager: 컨텍스트 관리
  - Conversation: 대화 모델

- 메서드:
  1. chat(user_message: str) -> str:
     - 사용자 메시지를 받아 응답 반환
     - 전체 파이프라인 실행
     - 에러 처리 포함
     
  2. chat_stream(user_message: str) -> Iterator[str]:
     - 스트리밍 응답 반환
     
  3. reset_conversation():
     - 대화 초기화
     
  4. save_conversation(filepath: str):
     - 대화 저장
     
  5. load_conversation(filepath: str):
     - 대화 로드

- __init__에서 모든 컴포넌트 초기화
- 각 단계마다 로깅
- 성능 메트릭 수집 (응답 시간, 토큰 사용량)
- 타입 힌트와 docstring

컴포넌트는 의존성 주입으로 받을 수 있게 하되, 
기본값으로 표준 구현을 사용해줘.
```

#### 💡 프롬프트 작성 팁

- **의존성 주입 명시**: 어떤 컴포넌트를 주입받을지
- **파이프라인 설명**: 데이터 흐름 순서
- **에러 전파**: 어느 단계에서 에러 처리할지
- **확장성 고려**: 새 컴포넌트 추가가 쉽게

### 6단계: 실전 예제 작성

#### 📌 목표
완전한 대화 예제를 만들어 모든 기능을 테스트합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `examples/conversation_example.py` 생성 후:**

```
ConversationAgent를 사용하는 대화형 CLI 예제를 만들어줘.

기능:
- 무한 루프로 사용자 입력 받기
- "exit" 입력 시 종료
- "/save <파일명>" 명령으로 대화 저장
- "/load <파일명>" 명령으로 대화 로드
- "/reset" 명령으로 대화 초기화
- "/history" 명령으로 대화 기록 출력

구현:
- rich 라이브러리로 예쁜 출력
- 타이핑 효과 (스트리밍)
- 에러 처리
- 시그널 핸들링 (Ctrl+C)

사용 방법을 docstring에 포함해줘.
```

**파일: `examples/streaming_example.py` 생성 후:**

```
스트리밍 응답을 보여주는 예제를 만들어줘.

요구사항:
- ConversationAgent의 chat_stream 사용
- 실시간으로 토큰 출력
- 타이핑 효과처럼 보이게
- 응답 완료 후 소요 시간 표시
- 여러 질문을 순서대로 처리

rich 라이브러리의 Live display 사용해서 
멋진 UI로 만들어줘.
```

## 🎓 학습 정리

### 이 단계에서 배운 프롬프트 작성 기법

1. **파이프라인 설계**: 데이터 흐름을 명확히 정의
2. **컴포넌트 조합**: 여러 클래스의 협력 관계 설명
3. **비동기/스트리밍**: 특수한 실행 모델 요청
4. **성능 최적화**: 캐싱, 토큰 제한 등 요구사항

### 체크리스트 ✅

다음 파일들이 생성되었는지 확인하세요:

- [ ] `src/agent/models.py` - 메시지 모델
- [ ] `src/agent/message_processor.py` - 메시지 프로세서
- [ ] `src/agent/response_generator.py` - 응답 생성기
- [ ] `src/agent/context_manager.py` - 컨텍스트 매니저
- [ ] `src/agent/conversation_agent.py` - 통합 Agent
- [ ] `examples/conversation_example.py` - 대화 예제
- [ ] `examples/streaming_example.py` - 스트리밍 예제

### 확인 명령어

```bash
# 대화 예제 실행
uv run python examples/conversation_example.py

# 스트리밍 예제 실행
uv run python examples/streaming_example.py

# 타입 체크
uv run mypy src/agent/

# 테스트 실행 (다음 단계에서 작성)
uv run pytest tests/
```

## 🔄 다음 단계

메시지 처리와 응답 생성 기능이 완성되었습니다!

👉 [Step 04: 커스텀 기능 추가](../step-04/README.md)로 이동하여 플러그인과 고급 기능을 추가해봅시다.

## 💡 디버깅 프롬프트

### 응답 품질 개선

```
ResponseGenerator의 응답 품질을 개선해줘.

개선 사항:
- few-shot 예제 추가
- temperature 동적 조정
- 응답 후처리 (포매팅, 정제)
- 안전성 체크 (유해 콘텐츠 필터링)

설정으로 각 기능을 켜고 끌 수 있게 해줘.
```

### 성능 프로파일링

```
ConversationAgent에 성능 측정 기능을 추가해줘.

측정 항목:
- 각 단계별 소요 시간
- 토큰 사용량
- API 호출 횟수
- 메모리 사용량

데코레이터 패턴으로 구현하고,
결과를 JSON으로 export하는 기능도 추가해줘.
```

### 테스트 케이스 생성

```
MessageProcessor를 위한 포괄적인 테스트를 작성해줘.

pytest 사용:
- 정상 케이스
- 경계값 테스트
- 에러 케이스
- 보안 테스트 (인젝션 등)
- 파라미터화된 테스트

각 테스트는 given-when-then 주석으로 구조화해줘.
파일명: tests/test_message_processor.py
```

---

**대단합니다! 🎉 핵심 기능 구현 완료! 계속 진행하세요!**
