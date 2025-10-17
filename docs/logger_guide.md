# Logger Utility - 로깅 유틸리티

## 개요

Agent 프로젝트를 위한 간단하고 효과적인 로깅 유틸리티입니다. 표준 Python `logging` 모듈을 기반으로 하며, 선택적으로 `colorlog` 라이브러리를 통한 컬러 출력을 지원합니다.

## 주요 특징

- ✅ **표준 Python logging 모듈 사용**
- ✅ **일관된 로그 포맷**: `[시간] [레벨] [로거명] 메시지`
- ✅ **컬러 출력 지원** (colorlog 사용 시)
- ✅ **간단한 API**: 한 줄로 로거 설정
- ✅ **타입 힌트 완벽 지원**
- ✅ **중복 로그 방지**
- ✅ **다양한 로그 레벨 지원**

## 설치

### 기본 설치 (컬러 없음)

```bash
# 기본 Python logging만 사용
uv pip install python-dotenv pydantic
```

### 컬러 출력 지원 (권장)

```bash
# colorlog 라이브러리 추가
uv pip install colorlog
```

## 사용 방법

### 기본 사용

```python
from src.utils.logger import setup_logger

# 로거 생성 (기본 INFO 레벨)
logger = setup_logger(__name__)

logger.debug("디버그 메시지 (보이지 않음)")
logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")
logger.critical("치명적 오류")
```

**출력 예시:**
```
[2025-10-15 10:30:45] [INFO] [myapp] 정보 메시지
[2025-10-15 10:30:45] [WARNING] [myapp] 경고 메시지
[2025-10-15 10:30:45] [ERROR] [myapp] 에러 메시지
[2025-10-15 10:30:45] [CRITICAL] [myapp] 치명적 오류
```

### DEBUG 레벨로 설정

```python
from src.utils.logger import setup_logger

# DEBUG 레벨로 로거 생성
logger = setup_logger(__name__, level="DEBUG")

logger.debug("디버그 메시지 (이제 보임)")
logger.info("정보 메시지")
```

### 모듈별 다른 로그 레벨

```python
from src.utils.logger import setup_logger

# Agent 모듈은 INFO
agent_logger = setup_logger("agent", level="INFO")

# API 모듈은 DEBUG
api_logger = setup_logger("api", level="DEBUG")

# Utils 모듈은 WARNING만
utils_logger = setup_logger("utils", level="WARNING")

agent_logger.info("Agent initialized")      # 출력됨
api_logger.debug("API request details")     # 출력됨
utils_logger.info("This won't show")        # 출력 안됨
utils_logger.warning("Utils warning")       # 출력됨
```

### 예외 로깅

```python
logger = setup_logger(__name__)

try:
    result = 1 / 0
except ZeroDivisionError as e:
    logger.error(f"에러 발생: {e}")
    logger.exception("전체 스택 트레이스:")
```

**출력 예시:**
```
[2025-10-15 10:30:45] [ERROR] [myapp] 에러 발생: division by zero
[2025-10-15 10:30:45] [ERROR] [myapp] 전체 스택 트레이스:
Traceback (most recent call last):
  File "example.py", line 5, in <module>
    result = 1 / 0
ZeroDivisionError: division by zero
```

### 구조화된 로깅

```python
logger = setup_logger(__name__)

# 추가 컨텍스트와 함께 로깅
logger.info(
    "User login successful",
    extra={
        "user_id": "user123",
        "session_id": "sess456",
        "ip_address": "192.168.1.1",
    }
)
```

### 전역 루트 로거 설정

애플리케이션 시작 시 한 번 호출하여 기본 로깅 설정:

```python
from src.utils.logger import configure_root_logger

# 애플리케이션 진입점에서 한 번만 호출
configure_root_logger("DEBUG")

# 이제 모든 모듈에서 기본 설정 사용 가능
import logging
logger = logging.getLogger(__name__)
logger.info("Using root logger configuration")
```

## API 레퍼런스

### `setup_logger(name: str, level: str = "INFO") -> logging.Logger`

새로운 로거를 생성하고 설정합니다.

**Parameters:**
- `name` (str): 로거 이름 (일반적으로 `__name__` 사용)
- `level` (str): 로그 레벨. 기본값은 `"INFO"`. 
  - 가능한 값: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

**Returns:**
- `logging.Logger`: 설정된 로거 인스턴스

**Raises:**
- `ValueError`: 잘못된 로그 레벨이 제공된 경우

**Example:**
```python
logger = setup_logger(__name__)
logger.info("Hello, World!")
```

### `get_logger(name: str) -> logging.Logger`

이미 생성된 로거를 이름으로 가져옵니다.

**Parameters:**
- `name` (str): 가져올 로거의 이름

**Returns:**
- `logging.Logger`: 로거 인스턴스

**Example:**
```python
# 다른 모듈에서 생성한 로거 가져오기
logger = get_logger("agent")
logger.info("Using existing logger")
```

### `configure_root_logger(level: str = "INFO") -> None`

전체 애플리케이션의 루트 로거를 설정합니다.

**Parameters:**
- `level` (str): 루트 로거의 로그 레벨. 기본값은 `"INFO"`

**Example:**
```python
# main.py 또는 __init__.py에서
configure_root_logger("DEBUG")
```

## 로그 레벨 가이드

| 레벨 | 사용 시기 | 예시 |
|------|----------|------|
| **DEBUG** | 디버깅 정보, 상세한 실행 흐름 | 함수 호출, 변수 값 |
| **INFO** | 일반적인 정보성 메시지 | 서버 시작, 작업 완료 |
| **WARNING** | 경고 (프로그램은 정상 실행) | 지원 중단 예정, 권장하지 않는 사용 |
| **ERROR** | 에러 (기능 실패했으나 프로그램 계속) | API 호출 실패, 파일 읽기 실패 |
| **CRITICAL** | 치명적 에러 (프로그램 중단 가능) | 데이터베이스 연결 실패, 메모리 부족 |

## 컬러 출력

`colorlog` 라이브러리가 설치되어 있으면 자동으로 컬러 출력이 활성화됩니다.

### 컬러 스킴

- 🔵 **DEBUG**: Cyan (청록색)
- 🟢 **INFO**: Green (녹색)
- 🟡 **WARNING**: Yellow (노란색)
- 🔴 **ERROR**: Red (빨간색)
- ⚪🔴 **CRITICAL**: Red with white background (빨강 배경 흰색)

### colorlog 설치

```bash
uv pip install colorlog

# 또는 pip
pip install colorlog
```

### 컬러 비활성화

`colorlog`를 설치하지 않으면 자동으로 일반 텍스트 출력으로 전환됩니다.

## BaseAgent와 함께 사용

`BaseAgent` 클래스에서 로거 사용 예시:

```python
from src.utils.logger import setup_logger
from src.agent.base_agent import BaseAgent
from src.config.agent_config import AgentConfig

# 로거 설정
logger = setup_logger(__name__)

# Agent 생성
config = AgentConfig.from_env()
agent = BaseAgent(config)

# 로깅과 함께 Agent 사용
logger.info("Sending message to agent")
response = await agent.run("Hello!")
logger.info(f"Received response: {response[:50]}...")
```

## 프로덕션 환경 설정

### 환경별 로그 레벨

```python
import os
from src.utils.logger import setup_logger

# 환경 변수로 로그 레벨 제어
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = setup_logger(__name__, level=log_level)
```

**.env 파일:**
```bash
# 개발 환경
LOG_LEVEL=DEBUG

# 프로덕션 환경
LOG_LEVEL=WARNING
```

### 민감 정보 로깅 주의

```python
# ❌ 나쁜 예 - API 키 노출
logger.info(f"Using API key: {api_key}")

# ✅ 좋은 예 - 마스킹
logger.info(f"Using API key: {api_key[:8]}...")

# ✅ 좋은 예 - 민감 정보 제외
logger.info("API authentication successful")
```

## 예제 실행

전체 예제는 `examples/logger_example.py`에서 확인할 수 있습니다.

```bash
# 예제 실행
python examples/logger_example.py
```

## 트러블슈팅

### 로그가 중복으로 출력됨

**원인:** 로거를 여러 번 설정했거나 핸들러가 중복 추가됨

**해결:**
```python
# setup_logger는 자동으로 중복 핸들러를 제거합니다
logger = setup_logger(__name__)  # 안전하게 여러 번 호출 가능
```

### 로그가 출력되지 않음

**원인:** 로그 레벨이 너무 높게 설정됨

**해결:**
```python
# 레벨을 낮춰서 더 많은 로그 보기
logger = setup_logger(__name__, level="DEBUG")
```

### 컬러가 표시되지 않음

**원인:** colorlog가 설치되지 않았거나 터미널이 컬러를 지원하지 않음

**해결:**
```bash
# colorlog 설치
uv pip install colorlog

# 또는 컬러 없이 사용 (문제 없음)
```

## 모범 사례

1. **모듈 이름 사용**: 항상 `__name__`을 로거 이름으로 사용
   ```python
   logger = setup_logger(__name__)
   ```

2. **적절한 레벨 선택**: 메시지 중요도에 맞는 레벨 사용

3. **구조화된 정보**: `extra` 매개변수로 추가 컨텍스트 제공

4. **예외는 exception()**: 스택 트레이스가 필요하면 `logger.exception()` 사용

5. **민감 정보 보호**: API 키, 비밀번호 등은 로그에 출력하지 않기

## 참고 자료

- [Python logging 공식 문서](https://docs.python.org/3/library/logging.html)
- [colorlog GitHub](https://github.com/borntyping/python-colorlog)
- [프로젝트 코딩 규칙](.github/copilot-instructions.md)

## 라이선스

MIT License
