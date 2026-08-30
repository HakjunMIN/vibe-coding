# Examples Directory

이 디렉토리에는 Vibe Coding Agent 프로젝트의 다양한 사용 예제가 포함되어 있습니다.

## 📁 파일 목록

### 1. `basic_usage.py` ⭐ 시작하기
Microsoft Agent Framework를 사용한 기본 예제입니다.

**주요 기능:**
- ✅ Non-streaming 응답 (기본 메시지 처리)
- ✅ Streaming 응답 (실시간 토큰 출력)
- ✅ Multi-turn 대화 (컨텍스트 유지)
- ✅ 에러 핸들링
- ✅ 커스텀 모델/배포 설정

**실행 방법:**
```bash
# .env 파일 설정 후
python examples/basic_usage.py
```

**패턴:**
```python
from agent_framework.azure import AzureOpenAIChatClient

chat_client = AzureOpenAIChatClient()
agent = chat_client.create_agent(
    name="BasicAgent",
    instructions="You are a helpful assistant."
)
result = await agent.run("Hello!")
```

### 2. `base_agent_example.py`
BaseAgent 클래스를 사용한 예제입니다.

**주요 기능:**
- BaseAgent 생성 및 사용
- AgentConfig를 통한 설정
- 스트리밍 응답
- 상태 초기화

### 3. `logger_example.py`
로깅 유틸리티 사용 예제입니다.

**주요 기능:**
- 색상 로깅 (colorlog 지원)
- 다양한 로그 레벨
- 구조화된 로깅

### 4. `validators_example.py`
입력 검증 유틸리티 사용 예제입니다.

**주요 기능:**
- API 키 검증
- 메시지 검증 및 sanitization
- XSS 방지

## 🚀 빠른 시작

### 환경 설정

1. `.env` 파일 생성:
```bash
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4
```

2. 의존성 설치:
```bash
uv sync
source .venv/bin/activate  # macOS/Linux
```

### 예제 실행

```bash
# 기본 사용 예제 (권장)
python examples/basic_usage.py

# BaseAgent 예제
python examples/base_agent_example.py

# 로거 예제
python examples/logger_example.py

# 검증 예제
python examples/validators_example.py

# 고급 예제
python examples/advanced_agent.py
```

## 📚 추가 문서

자세한 내용은 `docs/` 디렉토리를 참조하세요:

- `docs/base_agent_guide.md` - BaseAgent 완전 가이드
- `docs/logger_guide.md` - 로깅 가이드
- `docs/validators_guide.md` - 입력 검증 가이드

## 🎯 학습 경로

1. **시작**: `basic_usage.py` - Microsoft Agent Framework 기본
2. **심화**: `base_agent_example.py` - 커스텀 래퍼 클래스
3. **유틸리티**: `logger_example.py`, `validators_example.py` - 지원 도구

## 💡 팁

- `basic_usage.py`는 공식 Microsoft Agent Framework 패턴을 따릅니다
- 프로덕션에서는 환경 변수를 사용하여 API 키를 관리하세요
- 에러 핸들링 예제를 참고하여 안정적인 코드를 작성하세요
- 스트리밍은 긴 응답에 유용하지만 모든 경우에 필요한 것은 아닙니다

## 🔗 참고 자료

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [Project README](../../README.md)
