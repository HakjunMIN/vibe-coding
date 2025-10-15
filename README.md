# 🎵 Vibe Coding: AI Agent 만들기 실습

GitHub Copilot을 활용한 바이브코딩(Vibe Coding)으로 AI Agent를 만드는 실습 리포지토리입니다.

## 📖 소개

이 리포지토리는 **프롬프트 작성**에 집중하여, GitHub Copilot과 함께 AI Agent를 단계별로 만들어가는 실습 과정을 제공합니다. 직접 코드를 타이핑하는 대신, **올바른 프롬프트를 작성**하여 Copilot이 코드를 생성하도록 하는 방법을 배웁니다.

### 주요 특징

- 🤖 **Microsoft Agent Framework** 기반
- 🐍 **Python** 프로젝트
- 📦 **uv** 패키지 관리자 사용
- 💬 **프롬프트 중심** 학습 방식
- 🎨 **커스텀 코딩 규칙** 적용 예제 포함

## 🎯 학습 목표

이 실습을 마치면 다음을 할 수 있게 됩니다:

1. GitHub Copilot을 활용한 효과적인 프롬프트 작성법 이해
2. Microsoft Agent Framework를 사용한 AI Agent 구조 설계
3. 커스텀 코딩 규칙을 적용하여 일관된 코드 생성
4. 단계별로 복잡도를 높여가며 AI Agent 구현

## 📋 사전 요구사항

### 필수 설치

1. **Python 3.11 이상**
   ```bash
   python --version
   ```

2. **uv 패키지 관리자**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Visual Studio Code**
   - [다운로드](https://code.visualstudio.com/)

4. **GitHub Copilot**
   - VS Code에서 GitHub Copilot 확장 설치
   - GitHub Copilot 구독 필요

### 권장 VS Code 확장

- GitHub Copilot
- GitHub Copilot Chat
- Python
- Pylance

## 🚀 시작하기

### 1. 리포지토리 클론

```bash
git clone https://github.com/yourusername/vibe-coding.git
cd vibe-coding
```

### 2. Python 환경 설정

```bash
# Python 버전 확인
uv python install 3.11

# 가상 환경 생성 및 활성화
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
```

### 3. 의존성 설치

```bash
uv pip install -e .
```

## 📚 실습 단계

이 실습은 5단계로 구성되어 있으며, 각 단계마다 **어떤 프롬프트를 작성해야 하는지** 자세히 안내합니다.

### [Step 01: 프로젝트 초기 설정](./steps/step-01/README.md)
- 프로젝트 구조 생성을 위한 프롬프트 작성법
- 기본 의존성 추가 프롬프트
- 환경 설정 파일 생성 가이드

### [Step 02: 기본 Agent 구조 만들기](./steps/step-02/README.md)
- Microsoft Agent Framework SDK를 사용한 Agent 생성 프롬프트
- ChatAgent와 ChatClient 구조 이해
- async/await 패턴 적용 방법

### [Step 03: 메시지 처리 및 응답 생성](./steps/step-03/README.md)
- 메시지 핸들러 구현 프롬프트
- LLM 통합을 위한 프롬프트 작성
- 대화 컨텍스트 관리 구현 요청

### [Step 04: 커스텀 기능 추가](./steps/step-04/README.md)
- 도구(Tools) 시스템 구현 프롬프트
- Function Calling 패턴 적용
- 외부 API 통합 도구 작성 방법

### [Step 05: 테스트 및 배포](./steps/step-05/README.md)
- 유닛 테스트 생성 프롬프트
- 통합 테스트 작성 요청
- 배포 설정 파일 생성 가이드

## 🎨 커스텀 코딩 규칙

이 프로젝트에는 일관된 코드 스타일을 유지하기 위한 커스텀 코딩 규칙이 적용되어 있습니다.

### Copilot Instructions 설정

`.github/copilot-instructions.md` 파일에 커스텀 규칙이 정의되어 있습니다:

- 코드 스타일 가이드
- 네이밍 컨벤션
- 주석 작성 규칙
- 에러 핸들링 패턴
- 로깅 규칙

자세한 내용은 [커스텀 코딩 규칙 가이드](./.github/copilot-instructions.md)를 참조하세요.

## 💡 바이브코딩 팁

### 좋은 프롬프트 작성 원칙

1. **구체적으로 작성하기**
   - ❌ "함수 만들어줘"
   - ✅ "사용자 입력을 검증하는 validate_user_input 함수를 만들어줘. email과 name 필드를 체크하고, 잘못된 경우 ValueError를 발생시켜야 해"

2. **컨텍스트 제공하기**
   - 현재 파일의 다른 코드 참조
   - 사용 중인 라이브러리 명시
   - 기대하는 입출력 예시 제공

3. **단계적으로 요청하기**
   - 복잡한 기능은 여러 단계로 나누어 요청
   - 각 단계의 결과를 확인하고 다음 단계로 진행

4. **코딩 규칙 언급하기**
   - "프로젝트의 코딩 규칙을 따라서..."
   - "타입 힌트를 포함해서..."
   - "docstring을 Google 스타일로..."

### 효과적인 Copilot 사용법

- **Inline 제안**: 코드 작성 중 자동 완성 활용
- **Copilot Chat**: 복잡한 로직은 Chat으로 설명 요청
- **코드 리팩토링**: 기존 코드를 선택하고 개선 요청
- **테스트 생성**: 함수를 선택하고 테스트 케이스 생성 요청

## 🗂️ 프로젝트 구조

```
vibe-coding/
├── .github/
│   ├── copilot-instructions.md    # Copilot 커스텀 규칙
│   └── .copilotignore              # Copilot이 무시할 파일
├── steps/
│   ├── step-01/
│   │   └── README.md               # 1단계 가이드
│   ├── step-02/
│   │   └── README.md               # 2단계 가이드
│   ├── step-03/
│   │   └── README.md               # 3단계 가이드
│   ├── step-04/
│   │   └── README.md               # 4단계 가이드
│   └── step-05/
│       └── README.md               # 5단계 가이드
├── src/
│   └── agent/                      # Agent 소스 코드
├── tests/                          # 테스트 코드
├── .python-version                 # Python 버전
├── pyproject.toml                  # 프로젝트 설정
├── uv.lock                         # 의존성 락 파일
└── README.md                       # 이 파일
```

## 🤝 기여하기

이 프로젝트는 학습 목적으로 만들어졌습니다. 개선 사항이나 추가 단계에 대한 아이디어가 있다면 이슈나 PR을 환영합니다!

## 📝 라이선스

MIT License

## 🔗 참고 자료

- [Microsoft Agent Framework 공식 리포지토리](https://github.com/microsoft/agent-framework)
- [Microsoft Agent Framework Python SDK](https://github.com/microsoft/agent-framework/tree/main/python)
- [공식 Getting Started 샘플](https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started)
- [GitHub Copilot 문서](https://docs.github.com/en/copilot)
- [uv 문서](https://docs.astral.sh/uv/)
- [Python 타입 힌팅 가이드](https://docs.python.org/3/library/typing.html)

## 💬 질문 및 지원

질문이 있거나 도움이 필요하면:
- GitHub Issues에 질문 등록
- Discussions에서 커뮤니티와 소통

---

**Happy Vibe Coding! 🎵✨**
