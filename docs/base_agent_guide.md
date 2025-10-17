# BaseAgent - Microsoft Agent Framework 기반 AI Agent

## 개요

`BaseAgent`는 Microsoft Agent Framework를 사용하여 구현된 AI Agent 기본 클래스입니다. Azure OpenAI 또는 OpenAI를 백엔드로 사용하며, 스트리밍 및 비스트리밍 모드를 지원합니다.

## 주요 특징

- ✅ **Microsoft Agent Framework 공식 SDK 사용**
- ✅ **Azure OpenAI 지원** (API Key 인증)
- ✅ **비동기(async/await) 패턴**
- ✅ **스트리밍 응답 지원**
- ✅ **타입 힌트 완벽 지원**
- ✅ **구조화된 로깅**
- ✅ **에러 핸들링**
- ✅ **Google 스타일 Docstring**

## 설치

```bash
# UV 사용 (권장)
uv pip install agent-framework python-dotenv pydantic

# 또는 pip 사용
pip install agent-framework python-dotenv pydantic
```

## 환경 변수 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```bash
# Azure OpenAI 설정 (필수)
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com

# 선택 사항
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4  # 기본값: gpt-4
AGENT_NAME=VibeCodingAgent          # 기본값: VibeCodingAgent
TEMPERATURE=0.7                      # 기본값: 0.7
MAX_TOKENS=2000                      # 기본값: 2000
TIMEOUT=60                           # 기본값: 60
```

## 사용 방법

### 기본 사용

```python
import asyncio
from src.agent.base_agent import BaseAgent
from src.config.agent_config import AgentConfig

async def main():
    # 환경 변수에서 설정 로드
    config = AgentConfig.from_env()
    
    # Agent 생성
    agent = BaseAgent(config)
    
    # 메시지 전송
    response = await agent.run("Hello, how are you?")
    print(response)

asyncio.run(main())
```

### 스트리밍 응답

```python
async def streaming_example():
    config = AgentConfig.from_env()
    agent = BaseAgent(config)
    
    # 스트리밍으로 응답 받기
    async for chunk in agent.run_stream("Tell me a story"):
        print(chunk, end="", flush=True)

asyncio.run(streaming_example())
```

### 대화 히스토리 관리 및 초기화

```python
async def conversation_example():
    config = AgentConfig.from_env()
    agent = BaseAgent(config)
    
    # 첫 번째 대화
    response1 = await agent.run("My name is Alice")
    print(response1)
    
    # 두 번째 대화 (이전 대화 기억)
    response2 = await agent.run("What is my name?")
    print(response2)  # "Your name is Alice" 같은 응답
    
    # Agent 상태 초기화
    agent.reset()
    
    # 초기화 후 대화 (이전 대화 잊음)
    response3 = await agent.run("What is my name?")
    print(response3)  # "I don't know your name" 같은 응답

asyncio.run(conversation_example())
```

## API 레퍼런스

### BaseAgent

AI Agent의 기본 구현 클래스입니다.

#### `__init__(config: AgentConfig)`

Agent를 초기화합니다.

**Parameters:**
- `config` (AgentConfig): Agent 설정 객체

**Raises:**
- `AgentInitializationError`: Agent 초기화 실패 시

#### `async run(message: str) -> str`

메시지를 처리하고 응답을 반환합니다.

**Parameters:**
- `message` (str): 사용자 입력 메시지

**Returns:**
- `str`: Agent의 응답

**Raises:**
- `ValueError`: 빈 메시지인 경우
- `AgentExecutionError`: 메시지 처리 실패 시

**Example:**
```python
response = await agent.run("What is AI?")
```

#### `async run_stream(message: str) -> AsyncIterator[str]`

메시지를 처리하고 스트리밍으로 응답을 반환합니다.

**Parameters:**
- `message` (str): 사용자 입력 메시지

**Yields:**
- `str`: Agent 응답의 청크

**Raises:**
- `ValueError`: 빈 메시지인 경우
- `AgentExecutionError`: 스트리밍 실패 시

**Example:**
```python
async for chunk in agent.run_stream("Tell me a story"):
    print(chunk, end="")
```

#### `reset() -> None`

Agent의 상태를 초기화합니다.

대화 히스토리를 지우고 Agent를 초기 상태로 되돌립니다.

**Raises:**
- `AgentInitializationError`: Agent 재생성 실패 시

**Example:**
```python
agent.reset()
```

#### `get_conversation_history() -> list[dict[str, Any]]`

대화 히스토리를 반환합니다.

**Returns:**
- `list[dict[str, Any]]`: 대화 메시지 리스트

**Note:**
- Microsoft Agent Framework는 Thread 상태를 내부적으로 관리합니다.
- 영구적인 Thread 관리가 필요한 경우 `AgentThread`를 직접 사용하세요.

**Example:**
```python
history = agent.get_conversation_history()
```

## 예외 처리

### AgentError

모든 Agent 관련 예외의 기본 클래스입니다.

### AgentInitializationError

Agent 초기화 실패 시 발생하는 예외입니다.

```python
try:
    agent = BaseAgent(config)
except AgentInitializationError as e:
    print(f"Failed to initialize agent: {e}")
```

### AgentExecutionError

Agent 실행 중 오류 발생 시 발생하는 예외입니다.

```python
try:
    response = await agent.run("Hello")
except AgentExecutionError as e:
    print(f"Failed to execute: {e}")
```

## 로깅

BaseAgent는 구조화된 로깅을 사용합니다.

```python
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Agent 사용
agent = BaseAgent(config)
# 로그 출력: "Initializing BaseAgent"
```

## 실전 예제

전체 예제는 `examples/base_agent_example.py`를 참조하세요.

```bash
# 예제 실행
python examples/base_agent_example.py
```

## 참고 자료

- [Microsoft Agent Framework - Python](https://github.com/microsoft/agent-framework/tree/main/python)
- [Getting Started Samples](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started)
- [프로젝트 코딩 규칙](.github/copilot-instructions.md)

## 라이선스

MIT License
