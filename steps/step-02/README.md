# Step 02: 기본 Agent 구조 만들기

## 🎯 학습 목표

이 단계에서는 Microsoft Agent Framework(Autogen)를 사용한 기본 AI Agent 클래스 구조를 생성합니다. 프롬프트를 통해 Agent의 핵심 컴포넌트를 만드는 방법을 배웁니다.

## 📝 이 단계에서 배울 내용

- Agent 클래스 생성을 위한 프롬프트
- 설정 관리 클래스 구현 요청
- 타입 안전성을 고려한 코드 생성
- Pydantic을 활용한 데이터 검증

## 🚀 시작하기

### 1단계: Agent 설정 클래스 생성

#### 📌 목표
Pydantic을 사용한 Agent 설정 클래스를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/config/agent_config.py` 생성 후 Copilot Chat:**

```
AI Agent를 위한 설정 클래스를 Pydantic BaseModel로 만들어줘.
AzureOpenAI를 사용할 것이므로 여기에 필요한 클래스들을 사용해 (예: AzureOpenAIClient)

요구사항:
- 클래스명: AgentConfig
- 필드:
  - agent_name: Agent 이름 (기본값: "VibeCodingAgent")
  - model: LLM 모델명 (기본값: "gpt-4")
  - temperature: 온도 설정 0.0~2.0 (기본값: 0.7)
  - max_tokens: 최대 토큰 수 (기본값: 2000)
  - api_key: OpenAI API 키 (필수, SecretStr 타입)
  - timeout: API 타임아웃 초 (기본값: 60)
  - system_message: 시스템 메시지 (선택)

- 검증 로직:
  - temperature는 0.0~2.0 범위
  - max_tokens는 1~32000 범위
  - timeout은 1~300 범위

- 환경 변수에서 로드하는 클래스 메서드 from_env() 추가
- Python 타입 힌트 모두 포함
- Google 스타일 docstring 추가
```

#### 💡 프롬프트 작성 팁

- **Pydantic 기능 명시**: validation, field 등 사용할 기능 지정
- **타입 명확히**: SecretStr, Optional 등 정확한 타입 요청
- **검증 조건 상세히**: 범위, 필수 여부 등
- **메서드 요구사항**: 클래스 메서드나 특별한 동작 설명

#### ✅ 예상 결과

```python
from pydantic import BaseModel, Field, field_validator, SecretStr
from typing import Optional
import os

class AgentConfig(BaseModel):
    """AI Agent 설정 클래스.
    
    Pydantic을 사용하여 Agent 설정을 검증하고 관리합니다.
    """
    
    agent_name: str = Field(
        default="VibeCodingAgent",
        description="Agent의 이름"
    )
    model: str = Field(
        default="gpt-4",
        description="사용할 LLM 모델"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0-2.0)"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=32000,
        description="최대 토큰 수"
    )
    api_key: SecretStr = Field(
        description="OpenAI API 키"
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="API 타임아웃 (초)"
    )
    system_message: Optional[str] = Field(
        default=None,
        description="시스템 메시지"
    )
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """환경 변수에서 설정을 로드합니다.
        
        Returns:
            AgentConfig: 환경 변수로부터 생성된 설정 객체
            
        Raises:
            ValueError: 필수 환경 변수가 없을 때
        """
        return cls(
            agent_name=os.getenv("AGENT_NAME", "VibeCodingAgent"),
            model=os.getenv("MODEL", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            timeout=int(os.getenv("TIMEOUT", "60")),
            system_message=os.getenv("SYSTEM_MESSAGE"),
        )
```

### 2단계: 기본 Agent 클래스 생성

#### 📌 목표
Microsoft Agent Framework을 사용한 기본 Agent 클래스를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/base_agent.py` 생성 후 Copilot Chat:**

```
Microsoft Agent Framework를 사용하는 AI Agent 기본 클래스를 만들어줘.

참고: https://github.com/microsoft/agent-framework/tree/main/python

요구사항:
- 클래스명: BaseAgent
- agent_framework의 ChatAgent 사용
- __init__ 메서드:
  - config: AgentConfig 객체를 받음
  - OpenAIChatClient 또는 AzureOpenAIChatClient 생성
  - ChatAgent 인스턴스 생성
  
- 메서드:
  - async run(message: str) -> str: 메시지 처리 및 응답 반환
  - async run_stream(message: str) -> AsyncIterator[str]: 스트리밍 응답
  - reset(): Agent 상태 초기화
  - get_conversation_history() -> list: 대화 기록 반환
  
- 특징:
  - 모든 메서드에 타입 힌트
  - async/await 패턴 사용
  - 에러 핸들링 포함 (try-except)
  - 로깅 추가 (logging 모듈)
  - Google 스타일 docstring
  
프로젝트의 AgentConfig 클래스를 import해서 사용하고,
공식 샘플의 패턴을 따라서 구현해줘.
```

#### 💡 프롬프트 작성 팁

- **상속 관계 명시**: 어떤 클래스를 상속할지
- **의존성 명확히**: 다른 모듈의 클래스 사용 시 명시
- **에러 처리 요청**: try-except, 로깅 등
- **문서화 요구**: docstring 스타일 지정

#### 📋 추가 프롬프트 (Inline)

파일 내에서 각 메서드를 작성할 때 주석으로 프롬프트를 남길 수 있습니다:

```python
class BaseAgent(AssistantAgent):
    def __init__(self, config: AgentConfig):
        # TODO: AgentConfig에서 설정을 추출하고 AssistantAgent 초기화
        # system_message, llm_config, name 등을 설정해야 함
```

Copilot이 자동으로 구현을 제안합니다.

### 3단계: Agent Factory 패턴 구현

#### 📌 목표
Agent 생성을 담당하는 Factory 클래스를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/factory.py` 생성 후:**

```
Agent 생성을 위한 Factory 패턴 클래스를 만들어줘.

Microsoft Agent Framework 패턴 참고:
- https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents

요구사항:
- 클래스명: AgentFactory
- Singleton 패턴으로 구현
- 메서드:
  - create_agent(config: AgentConfig) -> ChatAgent: Agent 생성
  - create_from_env() -> ChatAgent: 환경 변수에서 Agent 생성
  
- 기능:
  - ChatAgent 인스턴스 생성 (agent_framework 사용)
  - OpenAIChatClient 또는 AzureOpenAIChatClient 선택
  - Agent 인스턴스 캐싱 (같은 설정이면 재사용)
  - 설정 검증
  - 생성 로깅
  
- 타입 힌트와 docstring 포함
- AgentConfig를 import해서 사용
- async 메서드로 구현

Singleton 패턴은 __new__ 메서드를 오버라이드해서 구현해줘.
공식 샘플의 agent 생성 패턴을 따라줘.
```

#### 💡 프롬프트 작성 팁

- **디자인 패턴 명시**: Singleton, Factory 등
- **구현 방법 힌트**: __new__, __init__ 등
- **최적화 요구**: 캐싱, 재사용 등
- **의존성 관계**: 어떤 클래스를 사용할지

### 4단계: 유틸리티 함수 생성

#### 📌 목표
Agent에서 사용할 공통 유틸리티 함수를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/utils/logger.py` 생성 후:**

```
Agent 프로젝트를 위한 로깅 유틸리티를 만들어줘.

요구사항:
- 함수: setup_logger(name: str, level: str = "INFO") -> logging.Logger
- 로그 형식: [시간] [레벨] [로거명] 메시지
- 콘솔에 스트리밍으로만 출력
- 색상 지원 (colorlog 라이브러리 사용 시도, 없으면 기본)

Python logging 모듈 표준 사용해줘.
```

**파일: `src/utils/validators.py` 생성 후:**

```
입력 검증을 위한 유틸리티 함수들을 만들어줘.

필요한 함수:
1. validate_api_key(key: str) -> bool: API 키 형식 검증
2. validate_message(message: str, max_length: int = 4000) -> bool: 메시지 검증
3. sanitize_input(text: str) -> str: 입력 문자열 정제

각 함수:
- 타입 힌트 포함
- docstring으로 검증 규칙 설명
- ValueError 발생 (검증 실패 시)
- 유닛 테스트 작성하기 쉽도록 순수 함수로

정규표현식 사용이 필요하면 re 모듈 활용해줘.
```

### 5단계: __init__.py 업데이트

#### 📌 목표
패키지 import를 쉽게 하기 위해 __init__.py를 업데이트합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/__init__.py` 열고:**

```
이 패키지의 주요 클래스들을 import해서 외부에서 쉽게 사용할 수 있도록 __init__.py를 작성해줘.

현재 패키지 구조:
- base_agent.py: BaseAgent 클래스
- factory.py: AgentFactory 클래스

__all__에도 추가해서 명시적으로 export해줘.
패키지 버전과 작성자 정보도 __version__, __author__로 추가해줘.
```

**파일: `src/config/__init__.py` 열고:**

```
config 패키지의 __init__.py를 작성해줘.

현재 파일:
- agent_config.py: AgentConfig 클래스

AgentConfig를 import하고 __all__에 추가해줘.
```

### 6단계: 간단한 실행 예제 생성

#### 📌 목표
Agent가 제대로 작동하는지 테스트할 수 있는 간단한 예제를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `examples/basic_usage.py` 생성 후:**

```
ChatAgent를 사용하는 간단한 예제 스크립트를 만들어줘.

Microsoft Agent Framework 샘플 참고:
- https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents/openai/openai_chat_client_basic.py

요구사항:
- .env에서 설정 로드
- AzureOpenAIChatClient 생성
- ChatAgent 생성 (instructions 포함)
- async/await 패턴 사용
- "안녕하세요, AI Agent 테스트입니다" 메시지 전송
- agent.run() 사용
- 응답 출력
- 스트리밍 예제도 포함 (agent.run_stream())

실행 방법과 예상 출력을 docstring에 포함해줘.
에러 처리도 포함하고, asyncio.run() 사용해줘.

예시 구조:
```python
import asyncio
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

async def main():
    agent = ChatAgent(
        chat_client=OpenAIChatClient(),
        instructions="You are a helpful assistant.",
    )
    result = await agent.run("안녕하세요, AI Agent 테스트입니다")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

공식 샘플의 패턴을 따라서 구현해줘.
```

## 🎓 학습 정리

### 이 단계에서 배운 프롬프트 작성 기법

1. **클래스 설계 프롬프트**: 상속, 메서드, 필드를 명확히 정의
2. **디자인 패턴 요청**: Singleton, Factory 등 패턴 명시
3. **의존성 관리**: 다른 모듈의 클래스 import 관계 설명
4. **코드 품질 요구**: 타입 힌트, docstring, 에러 처리

### 체크리스트 ✅

다음 파일들이 생성되었는지 확인하세요:

- [ ] `src/config/agent_config.py` - Agent 설정 클래스
- [ ] `src/agent/base_agent.py` - 기본 Agent 클래스
- [ ] `src/agent/factory.py` - Agent Factory
- [ ] `src/utils/logger.py` - 로깅 유틸리티
- [ ] `src/utils/validators.py` - 검증 유틸리티
- [ ] `src/agent/__init__.py` - Agent 패키지 init
- [ ] `src/config/__init__.py` - Config 패키지 init
- [ ] `examples/basic_usage.py` - 사용 예제

### 확인 명령어

```bash
# 타입 체크
uv run mypy src/

# 코드 포매팅 확인
uv run black --check src/

# 린팅
uv run ruff check src/

# 예제 실행 (API 키 설정 필요)
uv run python examples/basic_usage.py
```

## 🔄 다음 단계

기본 Agent 구조가 완성되었습니다!

👉 [Step 03: 메시지 처리 및 응답 생성](../step-03/README.md)로 이동하여 실제 대화 기능을 구현해봅시다.

## 💡 고급 프롬프트 팁

### 리팩토링 프롬프트

기존 코드를 개선하고 싶다면:

```
BaseAgent 클래스를 리팩토링해줘.

개선 사항:
- 비동기 처리 지원 (async/await)
- 타입 안전성 강화
- 에러 메시지 더 명확하게
- 테스트하기 쉬운 구조로 (의존성 주입)

기존 public API는 유지해야 해.
```

### 코드 설명 요청

생성된 코드를 이해하고 싶다면:

```
AgentFactory의 Singleton 패턴 구현을 단계별로 설명해줘.
왜 __new__ 메서드를 사용했는지, 어떻게 인스턴스를 재사용하는지 알려줘.
```

### 테스트 코드 생성

```
BaseAgent 클래스를 위한 유닛 테스트를 작성해줘.

pytest 사용:
- 테스트 픽스처로 mock AgentConfig 생성
- 각 public 메서드 테스트
- 에러 케이스도 테스트
- mock을 사용해서 외부 API 호출 없이 테스트

파일명: tests/test_base_agent.py
```

---

**훌륭합니다! 🚀 계속해서 다음 단계로 진행하세요!**
