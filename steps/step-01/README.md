# Step 01: 프로젝트 초기 설정

## 🎯 학습 목표

이 단계에서는 AI Agent 프로젝트의 기본 구조를 생성합니다. **직접 코드를 작성하는 것이 아니라**, GitHub Copilot에게 올바른 프롬프트를 작성하여 프로젝트 초기 설정을 완료하는 방법을 배웁니다.

## 📝 이 단계에서 배울 내용

- uv를 사용한 Python 프로젝트 초기화 프롬프트
- 프로젝트 구조 생성 요청 방법
- 의존성 파일 작성 프롬프트
- 기본 설정 파일 생성 가이드

## 🚀 시작하기

### 1단계: 프로젝트 디렉토리 구조 생성

#### 📌 목표
기본적인 Python 프로젝트 디렉토리 구조를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**Copilot Chat에 입력할 프롬프트:**

```
AI Agent 프로젝트를 위한 Python 디렉토리 구조를 만들고 싶어. 
다음 구조로 터미널 명령어를 생성해줘:

- src/agent: 메인 에이전트 코드
- src/config: 설정 파일
- src/utils: 유틸리티 함수
- tests: 테스트 코드
- docs: 문서

각 디렉토리에 __init__.py 파일도 포함해야 해.
macOS zsh 기준으로 한 번에 실행할 수 있는 명령어로 만들어줘.
```

#### 💡 프롬프트 작성 팁

- **구체적인 구조 명시**: 원하는 디렉토리 구조를 나열
- **플랫폼 지정**: macOS, Windows 등 OS를 명시
- **한 번에 실행 가능**: 여러 명령어를 조합할지 명확히 지정

#### ✅ 예상 결과

Copilot이 다음과 같은 명령어를 생성해줄 것입니다:

```bash
mkdir -p src/agent src/config src/utils tests docs && \
touch src/__init__.py src/agent/__init__.py src/config/__init__.py \
src/utils/__init__.py tests/__init__.py
```

### 2단계: pyproject.toml 생성

#### 📌 목표
uv를 사용하는 Python 프로젝트의 `pyproject.toml` 파일을 생성합니다.

#### ✍️ 프롬프트 작성 예시

**새 파일 `pyproject.toml` 생성 후 Copilot Chat:**

```
AI Agent 프로젝트를 위한 pyproject.toml 파일을 작성해줘.

요구사항:
- 프로젝트 이름: vibe-coding-agent
- 버전: 0.1.0
- Python 버전: >=3.11
- uv를 패키지 매니저로 사용
- 필수 의존성:
  - microsoft-autogen: Agent Framework
  - python-dotenv: 환경 변수 관리
  - pydantic: 데이터 검증
  - httpx: HTTP 클라이언트
- 개발 의존성:
  - pytest: 테스트
  - black: 코드 포매팅
  - ruff: 린팅
  - mypy: 타입 체킹

build-system은 hatchling을 사용해줘.
```

#### 💡 프롬프트 작성 팁

- **필수 정보 모두 제공**: 프로젝트명, 버전, Python 버전
- **의존성 명확히 분류**: 필수 vs 개발 의존성
- **각 패키지의 용도 설명**: Copilot이 적절한 버전을 선택하도록
- **빌드 시스템 명시**: setuptools, hatchling 등

#### ✅ 예상 결과

```toml
[project]
name = "vibe-coding-agent"
version = "0.1.0"
description = "AI Agent built with Microsoft Agent Framework"
requires-python = ">=3.11"
dependencies = [
    "pyautogen>=0.2.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### 3단계: Python 버전 고정

#### 📌 목표
`.python-version` 파일을 생성하여 프로젝트의 Python 버전을 명시합니다.

#### ✍️ 프롬프트 작성 예시

**Copilot Chat에 입력:**

```
.python-version 파일을 만들어서 Python 3.11.8을 사용하도록 설정해줘.
uv가 이 파일을 인식할 수 있도록 올바른 형식으로 작성해야 해.
```

#### ✅ 예상 결과

```
3.11.8
```

### 4단계: 환경 변수 템플릿 생성

#### 📌 목표
`.env.example` 파일을 만들어 필요한 환경 변수를 문서화합니다.

#### ✍️ 프롬프트 작성 예시

```
AI Agent 프로젝트를 위한 .env.example 파일을 만들어줘.

필요한 환경 변수:
- OPENAI_API_KEY: OpenAI API 키 (필수)
- AZURE_OPENAI_ENDPOINT: Azure OpenAI 엔드포인트 (선택)
- AZURE_OPENAI_KEY: Azure OpenAI 키 (선택)
- LOG_LEVEL: 로그 레벨 (기본값: INFO)
- AGENT_NAME: Agent 이름 (기본값: VibeCodingAgent)

각 변수에 대한 설명 주석도 포함해줘.
```

#### 💡 프롬프트 작성 팁

- **모든 환경 변수 나열**: 프로젝트에 필요한 모든 변수
- **필수/선택 명시**: 어떤 변수가 필수인지 표시
- **기본값 제공**: 가능한 경우 기본값 지정
- **설명 요청**: 주석으로 각 변수의 용도 설명

### 5단계: gitignore 파일 생성

#### 📌 목표
Python 프로젝트에 적합한 `.gitignore` 파일을 생성합니다.

#### ✍️ 프롬프트 작성 예시

```
Python 프로젝트를 위한 .gitignore 파일을 생성해줘.

포함해야 할 항목:
- Python 캐시 파일 (__pycache__, *.pyc)
- 가상 환경 (.venv, venv, env)
- IDE 설정 (.vscode, .idea)
- 환경 변수 파일 (.env)
- 테스트 커버리지 (.coverage, htmlcov)
- 빌드 산출물 (dist, build, *.egg-info)
- OS 관련 파일 (.DS_Store, Thumbs.db)
- uv 관련 파일 (uv.lock은 커밋하되, 캐시는 제외)

주석으로 각 섹션을 구분해줘.
```

### 6단계: 기본 README 업데이트

#### 📌 목표
현재 디렉토리의 README.md를 프로젝트에 맞게 업데이트합니다.

#### ✍️ 프롬프트 작성 예시

```
이 디렉토리(step-01 완료 후)를 위한 간단한 README.md 내용을 추가해줘.

포함할 내용:
- 프로젝트 설정 완료 상태
- 다음 단계에서 할 일 (Step 02로 이동)
- 현재까지 생성된 파일 목록
- 환경 설정 확인 명령어 (uv sync 등)

간결하고 명확하게 작성해줘.
```

## 🎓 학습 정리

### 이 단계에서 배운 프롬프트 작성 기법

1. **구조적 요청**: 디렉토리 구조를 명확히 정의
2. **상세한 스펙 제공**: 의존성, 버전, 설정 등 모든 정보 포함
3. **컨텍스트 제공**: 프로젝트 타입, 사용 도구, 목적 명시
4. **형식 지정**: 파일 형식, 주석 스타일 등 세부사항 요청

### 체크리스트 ✅

다음 파일들이 생성되었는지 확인하세요:

- [ ] `pyproject.toml` - 프로젝트 설정
- [ ] `.python-version` - Python 버전
- [ ] `.env.example` - 환경 변수 템플릿
- [ ] `.gitignore` - Git 무시 파일
- [ ] `src/agent/__init__.py` - Agent 패키지
- [ ] `src/config/__init__.py` - Config 패키지
- [ ] `src/utils/__init__.py` - Utils 패키지
- [ ] `tests/__init__.py` - Tests 패키지

### 확인 명령어

```bash
# 프로젝트 구조 확인
tree -L 3 -I '__pycache__|*.pyc|.venv'

# uv로 의존성 동기화
uv sync

# Python 버전 확인
uv run python --version
```

## 🔄 다음 단계

프로젝트 초기 설정이 완료되었습니다! 

👉 [Step 02: 기본 Agent 구조 만들기](../step-02/README.md)로 이동하여 실제 Agent 코드를 생성해봅시다.

## 💡 추가 팁

### 프롬프트를 다시 작성해야 할 때

Copilot의 결과가 만족스럽지 않다면:

1. **더 구체적으로**: 예시나 예상 결과 포함
2. **컨텍스트 추가**: 프로젝트 배경, 사용 기술 설명
3. **단계 나누기**: 복잡한 요청은 여러 단계로 분리
4. **레퍼런스 제공**: "Python 표준 라이브러리처럼..." 등

### 코드 리뷰 프롬프트

생성된 파일을 검토받고 싶다면:

```
생성된 pyproject.toml 파일을 리뷰해줘.
다음 관점에서 검토해줘:
- 빠진 필수 의존성이 있는지
- 버전 명시가 적절한지
- 보안상 문제가 있는 설정은 없는지
- 최신 Python 모범 사례를 따르는지
```

---

**잘하고 있습니다! 🎉 다음 단계로 계속 진행하세요!**
