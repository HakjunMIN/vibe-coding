# Validators - 입력 검증 유틸리티

## 개요

Agent 프로젝트를 위한 입력 검증 및 정제(sanitization) 유틸리티입니다. API 키, 사용자 메시지, 기타 입력값의 유효성을 검증하고 안전하게 처리합니다.

## 주요 특징

- ✅ **API 키 검증**: 형식 및 길이 확인
- ✅ **메시지 검증**: 길이 제한 및 내용 확인
- ✅ **입력 정제**: XSS, 인젝션 공격 방지
- ✅ **순수 함수**: 부작용 없는 테스트 가능한 구조
- ✅ **타입 힌트 완벽 지원**
- ✅ **상세한 에러 메시지**
- ✅ **예외/비예외 버전 모두 제공**

## 설치

```bash
# 기본 Python만 필요 (추가 의존성 없음)
uv pip install python-dotenv pydantic
```

## 사용 방법

### API 키 검증

#### 1. 예외 발생 버전 (권장)

```python
from src.utils.validators import validate_api_key

try:
    validate_api_key("sk-1234567890abcdefghij")
    print("API key is valid!")
except ValueError as e:
    print(f"Invalid API key: {e}")
```

**출력:**
```
API key is valid!
```

#### 2. 불린 반환 버전

```python
from src.utils.validators import is_valid_api_key

if is_valid_api_key("sk-1234567890abcdefghij"):
    print("API key is valid!")
else:
    print("API key is invalid")
```

### 메시지 검증

#### 기본 사용

```python
from src.utils.validators import validate_message

try:
    validate_message("Hello, AI!")
    print("Message is valid!")
except ValueError as e:
    print(f"Invalid message: {e}")
```

#### 커스텀 길이 제한

```python
from src.utils.validators import validate_message

# 최대 100자로 제한
try:
    validate_message("Short message", max_length=100)
    print("Message is valid!")
except ValueError as e:
    print(f"Invalid message: {e}")
```

#### 불린 반환 버전

```python
from src.utils.validators import is_valid_message

if is_valid_message("Hello!", max_length=1000):
    print("Message is valid!")
```

### 입력 정제 (Sanitization)

```python
from src.utils.validators import sanitize_input

# XSS 공격 시도 제거
dangerous_input = "<script>alert('xss')</script>Hello"
clean_input = sanitize_input(dangerous_input)
print(clean_input)  # "Hello"

# 과도한 공백 정리
messy_input = "  Too   many    spaces  "
clean_input = sanitize_input(messy_input)
print(clean_input)  # "Too many spaces"

# 이벤트 핸들러 제거
html_input = "Click <a onclick='steal()'>here</a>"
clean_input = sanitize_input(html_input)
print(clean_input)  # "Click <a >here</a>"
```

### 검증 + 정제 (한 번에)

```python
from src.utils.validators import validate_and_sanitize_message

try:
    # 정제 후 검증까지 한 번에
    clean_message = validate_and_sanitize_message(
        "  <script>bad</script> Hello World  ",
        max_length=1000
    )
    print(f"Clean message: '{clean_message}'")
    # "Clean message: 'Hello World'"
except ValueError as e:
    print(f"Error: {e}")
```

## API 레퍼런스

### `validate_api_key(key: str) -> bool`

API 키의 형식을 검증합니다.

**검증 규칙:**
- 빈 문자열 불가
- 길이: 20-200자
- 허용 문자: 영문, 숫자, `_`, `-`, `.`

**Parameters:**
- `key` (str): 검증할 API 키

**Returns:**
- `bool`: 항상 `True` (실패 시 예외 발생)

**Raises:**
- `ValueError`: 검증 실패 시 상세한 오류 메시지 포함

**Example:**
```python
validate_api_key("sk-1234567890abcdefghij")  # True
validate_api_key("invalid!")  # ValueError
validate_api_key("")  # ValueError: API key cannot be empty
```

---

### `is_valid_api_key(key: str) -> bool`

예외 없이 API 키 유효성을 확인합니다.

**Parameters:**
- `key` (str): 확인할 API 키

**Returns:**
- `bool`: 유효하면 `True`, 아니면 `False`

**Example:**
```python
if is_valid_api_key(user_input):
    # 처리 계속
    pass
else:
    print("Please provide a valid API key")
```

---

### `validate_message(message: str, max_length: int = 4000) -> bool`

사용자 메시지를 검증합니다.

**검증 규칙:**
- 빈 문자열/공백만 불가
- 최소 1자 이상 (공백 제외)
- 최대 길이 제한 (기본 4000자)

**Parameters:**
- `message` (str): 검증할 메시지
- `max_length` (int): 최대 허용 길이. 기본값 4000

**Returns:**
- `bool`: 항상 `True` (실패 시 예외 발생)

**Raises:**
- `ValueError`: 검증 실패 시

**Example:**
```python
validate_message("Hello!")  # True
validate_message("")  # ValueError: Message cannot be empty
validate_message("x" * 5000)  # ValueError: Message is too long
validate_message("OK", max_length=10)  # True
```

---

### `is_valid_message(message: str, max_length: int = 4000) -> bool`

예외 없이 메시지 유효성을 확인합니다.

**Parameters:**
- `message` (str): 확인할 메시지
- `max_length` (int): 최대 허용 길이

**Returns:**
- `bool`: 유효하면 `True`, 아니면 `False`

---

### `sanitize_input(text: str) -> str`

입력 문자열에서 위험한 내용을 제거합니다.

**정제 항목:**
- HTML `<script>` 태그
- JavaScript 프로토콜 핸들러
- 이벤트 핸들러 (`onclick`, `onload` 등)
- 제어 문자 및 null 바이트
- 과도한 공백 및 연속 줄바꿈

**Parameters:**
- `text` (str): 정제할 입력 문자열

**Returns:**
- `str`: 정제된 문자열

**Example:**
```python
sanitize_input("<script>alert('xss')</script>Hello")
# "Hello"

sanitize_input("  Too   many    spaces  ")
# "Too many spaces"

sanitize_input("Line1\n\n\n\nLine2")
# "Line1\n\nLine2"
```

---

### `validate_and_sanitize_message(message: str, max_length: int = 4000) -> str`

메시지를 정제하고 검증하는 편의 함수입니다.

**처리 순서:**
1. 입력 정제 (`sanitize_input`)
2. 정제된 결과 검증 (`validate_message`)

**Parameters:**
- `message` (str): 처리할 메시지
- `max_length` (int): 최대 허용 길이

**Returns:**
- `str`: 정제되고 검증된 메시지

**Raises:**
- `ValueError`: 정제 후에도 검증 실패 시

**Example:**
```python
result = validate_and_sanitize_message("  <script>bad</script> Hello  ")
# "Hello"
```

## 실전 사용 예제

### BaseAgent와 통합

```python
from src.utils.validators import validate_and_sanitize_message, validate_api_key
from src.agent.base_agent import BaseAgent
from src.config.agent_config import AgentConfig

# 1. API 키 검증
try:
    validate_api_key(api_key)
except ValueError as e:
    print(f"Invalid API key: {e}")
    exit(1)

# 2. Agent 생성
config = AgentConfig.from_env()
agent = BaseAgent(config)

# 3. 사용자 입력 처리
user_input = input("Your message: ")

try:
    # 입력 정제 및 검증
    clean_message = validate_and_sanitize_message(user_input, max_length=1000)
    
    # Agent에 전달
    response = await agent.run(clean_message)
    print(response)
    
except ValueError as e:
    print(f"Invalid input: {e}")
```

### 웹 API에서 사용

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.utils.validators import validate_and_sanitize_message, is_valid_api_key

app = FastAPI()

class ChatRequest(BaseModel):
    api_key: str
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    # API 키 검증
    if not is_valid_api_key(request.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 메시지 정제 및 검증
    try:
        clean_message = validate_and_sanitize_message(
            request.message,
            max_length=2000
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 처리 계속...
    return {"response": "OK"}
```

### 배치 처리

```python
from src.utils.validators import is_valid_message, sanitize_input

def process_messages(messages: list[str]) -> list[str]:
    """여러 메시지를 검증하고 정제합니다."""
    valid_messages = []
    
    for msg in messages:
        # 정제
        clean = sanitize_input(msg)
        
        # 검증 (예외 없는 버전)
        if is_valid_message(clean, max_length=500):
            valid_messages.append(clean)
        else:
            print(f"Skipping invalid message: {msg[:30]}...")
    
    return valid_messages

# 사용
messages = [
    "Valid message 1",
    "",  # 건너뜀
    "<script>bad</script>Valid message 2",
    "x" * 1000,  # 건너뜀 (너무 김)
]

clean_messages = process_messages(messages)
# ["Valid message 1", "Valid message 2"]
```

## 검증 규칙 상세

### API 키 형식

| 규칙 | 설명 | 예시 |
|------|------|------|
| **길이** | 20-200 자 | ✓ 최소 20자 필요 |
| **문자** | `a-zA-Z0-9_-.` | ✓ `sk-abc_123-test.key` |
| **공백** | 허용 안 됨 | ✗ `key with spaces` |
| **특수문자** | `_`, `-`, `.`만 | ✗ `key@with#special` |

### 메시지 검증

| 규칙 | 기본값 | 설명 |
|------|--------|------|
| **최소 길이** | 1자 | 공백 제외 후 계산 |
| **최대 길이** | 4000자 | 커스터마이징 가능 |
| **빈 문자열** | 불허 | 공백만 있어도 불허 |
| **제어 문자** | 정제 시 제거 | null, 제어 문자 등 |

### 정제 대상

| 항목 | 패턴 | 제거 결과 |
|------|------|----------|
| **Script 태그** | `<script>...</script>` | 완전 제거 |
| **JS 프로토콜** | `javascript:` | 제거 |
| **이벤트 핸들러** | `onclick=`, `onload=` 등 | 제거 |
| **Null 바이트** | `\x00` | 제거 |
| **제어 문자** | ASCII 0-31 (일부 제외) | 제거 |
| **과도한 공백** | 연속 공백 | 단일 공백으로 |
| **연속 줄바꿈** | 3개 이상 | 최대 2개로 |

## 보안 고려사항

### 1. XSS (Cross-Site Scripting) 방지

```python
# ✗ 위험한 입력
dangerous = "<script>alert('XSS')</script>"

# ✓ 안전하게 정제
safe = sanitize_input(dangerous)
# ""
```

### 2. SQL Injection 1차 방어

```python
# 주의: sanitize_input은 1차 방어일 뿐
# SQL 쿼리에는 항상 파라미터화된 쿼리 사용 필수!
user_input = sanitize_input(user_input)
# 그 다음 파라미터화된 쿼리 사용
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
```

### 3. Command Injection 방어

```python
# 시스템 명령에 사용자 입력을 절대 직접 전달하지 마세요
# sanitize_input으로 정제해도 위험합니다

# ✗ 절대 이렇게 하지 마세요
import os
os.system(f"ls {user_input}")  # 매우 위험!

# ✓ 검증된 입력만 사용
if user_input.isalnum():  # 추가 검증
    # 처리
    pass
```

## 에러 메시지 가이드

| 에러 메시지 | 원인 | 해결 방법 |
|------------|------|-----------|
| `API key cannot be empty` | 빈 문자열 또는 공백 | 유효한 API 키 제공 |
| `API key is too short` | 20자 미만 | 최소 20자 필요 |
| `API key contains invalid characters` | 허용되지 않는 문자 사용 | 영문, 숫자, `_`, `-`, `.`만 사용 |
| `Message cannot be empty` | 빈 메시지 | 내용 입력 필요 |
| `Message is too long` | 길이 초과 | 메시지 줄이기 또는 `max_length` 조정 |

## 성능 고려사항

모든 검증 함수는 **순수 함수**로 설계되어 있어 성능이 우수합니다:

- ✅ 부작용 없음 (side-effect free)
- ✅ 캐싱 가능
- ✅ 병렬 처리 안전
- ✅ 빠른 실행 (정규표현식 최적화)

```python
# 대량 처리 예시
from concurrent.futures import ThreadPoolExecutor
from src.utils.validators import sanitize_input

messages = ["msg1", "msg2", ...]  # 수천 개

with ThreadPoolExecutor() as executor:
    clean_messages = list(executor.map(sanitize_input, messages))
```

## 테스트 작성 예시

```python
import pytest
from src.utils.validators import validate_api_key, validate_message

def test_valid_api_key():
    """유효한 API 키는 True를 반환해야 함"""
    assert validate_api_key("sk-1234567890abcdefghij")

def test_invalid_api_key_empty():
    """빈 API 키는 ValueError 발생"""
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_api_key("")

def test_valid_message():
    """유효한 메시지는 True를 반환해야 함"""
    assert validate_message("Hello!")

def test_message_too_long():
    """긴 메시지는 ValueError 발생"""
    with pytest.raises(ValueError, match="too long"):
        validate_message("x" * 5000)
```

## 예제 실행

```bash
# 전체 예제 실행
python examples/validators_example.py
```

## 참고 자료

- [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [Python re 모듈](https://docs.python.org/3/library/re.html)
- [프로젝트 코딩 규칙](.github/copilot-instructions.md)

## 라이선스

MIT License
