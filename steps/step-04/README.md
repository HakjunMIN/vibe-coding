# Step 04: 커스텀 기능 추가

## 🎯 학습 목표

이 단계에서는 Agent에 플러그인 시스템, 외부 API 통합, 그리고 상태 관리 기능을 추가합니다. Agent를 확장 가능하고 실용적으로 만드는 방법을 배웁니다.

## 📝 이 단계에서 배울 내용

- 플러그인 아키텍처 설계 프롬프트
- 외부 API 통합 패턴
- 상태 관리 및 영속성 구현
- Function Calling 활용 방법

## 🚀 시작하기

### 1단계: 플러그인 시스템 설계

#### 📌 목표
확장 가능한 플러그인 시스템의 기반을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/plugins/base.py` 생성 후 Copilot Chat:**

```
Agent를 위한 플러그인 시스템을 만들어줘.

요구사항:
1. BasePlugin 추상 클래스:
   - name: 플러그인 이름 (property)
   - description: 플러그인 설명 (property)
   - version: 버전 (property)
   - enabled: 활성화 상태 (기본 True)
   
   - initialize(): 플러그인 초기화 (추상 메서드)
   - execute(context: dict) -> dict: 실행 (추상 메서드)
   - cleanup(): 정리 작업 (추상 메서드)
   - get_schema() -> dict: 플러그인 스키마 반환 (Function calling용)

2. PluginManager 클래스:
   - register_plugin(plugin: BasePlugin): 플러그인 등록
   - unregister_plugin(name: str): 플러그인 해제
   - get_plugin(name: str) -> BasePlugin: 플러그인 조회
   - list_plugins() -> list: 모든 플러그인 목록
   - execute_plugin(name: str, context: dict) -> dict: 플러그인 실행
   - load_from_directory(path: str): 디렉토리에서 플러그인 로드

- abc 모듈의 ABC, abstractmethod 사용
- 플러그인 로딩 시 검증 (스키마 체크)
- 에러 격리 (한 플러그인 실패가 전체 영향 없도록)
- 로깅 포함
- 타입 힌트와 docstring
```

#### 💡 프롬프트 작성 팁

- **추상화 수준 명시**: 인터페이스, 추상 클래스 등
- **라이프사이클 정의**: 초기화, 실행, 정리 순서
- **에러 격리 요구**: 플러그인 간 독립성
- **동적 로딩 명시**: 런타임에 플러그인 추가

### 2단계: 기본 플러그인 구현

#### 📌 목표
실제로 사용할 수 있는 유용한 플러그인들을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/tools/web_search.py` 생성 후:**

```
웹 검색 도구 함수를 만들어줘.

Microsoft Agent Framework 도구 패턴 참고:
- https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents/openai/openai_chat_client_with_function_tools.py

요구사항:
- 함수명: search_web
- 타입 힌트: Annotated 사용 (공식 샘플 패턴)
- 기능: 검색 쿼리를 받아 웹 검색 결과 반환
- API: DuckDuckGo (무료) 사용, duckduckgo-search 라이브러리
- 파라미터:
  - query: Annotated[str, Field(description="검색할 쿼리")]
  - max_results: Annotated[int, Field(description="최대 결과 수")] = 5
- 반환:
  - str: 검색 결과를 포맷팅한 문자열 (title, url, snippet)
- 에러 처리 (네트워크 실패 등)
- 결과 캐싱 (같은 쿼리)
- docstring 필수

예시:
```python
from typing import Annotated
from pydantic import Field

def search_web(
    query: Annotated[str, Field(description="The search query.")],
    max_results: Annotated[int, Field(description="Maximum number of results.")] = 5,
) -> str:
    \"\"\"Search the web using DuckDuckGo.\"\"\"
    # 구현
```

이 함수는 ChatAgent의 tools 파라미터에 직접 전달될 수 있어야 해.
```

**파일: `src/agent/plugins/calculator.py` 생성 후:**

```
계산기 플러그인을 만들어줘.

요구사항:
- 클래스명: CalculatorPlugin
- BasePlugin 상속
- 기능: 수식을 받아 계산 결과 반환
- 안전한 수식 평가 (ast.literal_eval 사용)
- 지원 연산:
  - 기본: +, -, *, /, **, %
  - 함수: sqrt, sin, cos, tan, log, exp
- execute 메서드:
  - context["expression"]: 수식 문자열
  - 결과를 숫자로 반환
- 에러 처리:
  - 잘못된 수식
  - 0으로 나누기
  - 지원하지 않는 함수
- 수식 검증 (위험한 코드 실행 방지)
- 타입 힌트와 docstring

Function calling 스키마도 작성해줘.
```

**파일: `src/agent/plugins/weather.py` 생성 후:**

```
날씨 정보 플러그인을 만들어줘.

요구사항:
- 클래스명: WeatherPlugin
- BasePlugin 상속
- API: OpenWeatherMap (무료 tier)
- execute 메서드:
  - context["location"]: 위치 (도시명 또는 좌표)
  - 현재 날씨 정보 반환
  - 결과: {temperature, description, humidity, wind_speed}
- 초기화 시 API 키 받기
- 위치 정규화 (다양한 형식 지원)
- 단위 변환 (섭씨/화씨)
- 결과 캐싱 (1시간)
- 에러 처리
- 타입 힌트와 docstring

httpx를 사용해서 비동기 요청도 지원해줘.
Function calling 스키마 포함.
```

### 3단계: 플러그인과 Agent 통합

#### 📌 목표
ConversationAgent에 플러그인 시스템을 통합합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/conversation_agent.py` 수정:**

```
ConversationAgent에 도구(tools) 시스템을 통합해줘.

Microsoft Agent Framework 도구 패턴 참고:
- https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started/agents

수정 사항:
1. __init__에 tools: list 파라미터 추가 (선택적)
   - 도구 함수 리스트를 받음
   
2. Agent 생성 시 tools 전달:
   ```python
   agent = ChatAgent(
       chat_client=client,
       instructions="You are a helpful assistant.",
       tools=[search_web, calculate, get_weather],  # 도구 등록
   )
   ```
   
3. async run 메서드:
   - ChatAgent.run()에 tools 전달 (Agent 레벨 또는 Run 레벨)
   - Agent가 자동으로 필요 시 도구 호출
   - 도구 실행 결과 자동 통합
   
4. async run_stream 메서드:
   - ChatAgent.run_stream()으로 스트리밍
   - 도구 호출 과정도 스트리밍으로 확인 가능

도구 사용 패턴:
- Agent 레벨: 생성 시 tools 전달, 모든 대화에서 사용 가능
- Run 레벨: 각 run() 호출 시 tools 전달, 특정 대화에만 사용

기존 코드는 최대한 유지하고, 도구는 선택적으로 사용되게 해줘.
타입 힌트와 docstring 업데이트.
공식 샘플의 패턴을 따라서 구현해줘.
```

#### 💡 프롬프트 작성 팁

- **기존 코드 보존**: 호환성 유지 요청
- **선택적 기능**: 플러그인 없이도 동작
- **통합 지점 명시**: 어디에 끼워넣을지
- **테스트 용이성**: 플러그인 mock 가능하게

### 4단계: 상태 관리 시스템

#### 📌 목표
Agent의 상태를 영속적으로 관리하는 시스템을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/state_manager.py` 생성 후:**

```
Agent 상태 관리를 위한 StateManager 클래스를 만들어줘.

요구사항:
1. AgentState 모델 (Pydantic):
   - session_id: 세션 ID
   - user_id: 사용자 ID (선택)
   - conversation: Conversation 객체
   - user_preferences: 사용자 설정 (dict)
   - plugin_data: 플러그인 데이터 (dict)
   - created_at, updated_at: 타임스탬프

2. StateManager 클래스:
   - create_session(user_id: Optional[str]) -> str: 새 세션 생성
   - get_session(session_id: str) -> AgentState: 세션 조회
   - update_session(session_id: str, state: AgentState): 세션 업데이트
   - delete_session(session_id: str): 세션 삭제
   - list_sessions(user_id: Optional[str]) -> list: 세션 목록
   
3. 저장소:
   - 기본: JSON 파일 (간단한 구현)
   - 확장: SQLite, Redis 지원 (추상화)
   - save(): 디스크에 저장
   - load(): 디스크에서 로드
   - auto_save: 자동 저장 (주기적)

4. 기능:
   - 세션 만료 (TTL)
   - 트랜잭션 (원자성)
   - 동시성 제어 (락)

- 스레드 세이프
- 타입 힌트와 docstring
- 각 저장소는 추상 인터페이스로
```

**파일: `src/agent/storage/base.py` 생성 후:**

```
상태 저장소를 위한 추상 인터페이스를 만들어줘.

요구사항:
- 추상 클래스: StorageBackend
- 메서드 (모두 추상):
  - save(key: str, value: dict): 저장
  - load(key: str) -> dict: 로드
  - delete(key: str): 삭제
  - exists(key: str) -> bool: 존재 확인
  - list_keys(pattern: str) -> list: 키 목록
  
- 각 메서드는 async 버전도 정의
- 에러 타입 정의 (StorageError, NotFoundError 등)
- 타입 힌트와 docstring

abc 모듈 사용해서 강제성 부여해줘.
```

### 5단계: 실용적인 예제 작성

#### 📌 목표
플러그인과 상태 관리를 모두 사용하는 실전 예제를 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `examples/advanced_agent.py` 생성 후:**

```
모든 기능을 사용하는 고급 Agent 예제를 만들어줘.

시나리오:
- 사용자 세션 관리
- 여러 플러그인 활성화 (웹 검색, 계산기, 날씨)
- 대화 중 자동으로 플러그인 사용
- 세션 저장 및 로드
- CLI 인터페이스

구현:
- 명령어:
  - /plugins: 사용 가능한 플러그인 목록
  - /enable <플러그인>: 플러그인 활성화
  - /disable <플러그인>: 플러그인 비활성화
  - /session save: 세션 저장
  - /session load <id>: 세션 로드
  - /session list: 세션 목록
  
- Function calling 모드로 자동 플러그인 사용
- 예쁜 UI (rich 라이브러리)
- 에러 처리
- 도움말 메시지

사용 시나리오 예시를 docstring에 포함해줘:
1. "서울 날씨 어때?"
2. "Python 공식 문서 찾아줘"
3. "123 * 456 계산해줘"
```

**파일: `examples/plugin_development.py` 생성 후:**

```
커스텀 플러그인 개발 가이드 예제를 만들어줘.

내용:
1. SimplePlugin 예제:
   - BasePlugin을 상속한 가장 간단한 플러그인
   - "Hello, World!" 반환
   
2. ParameterPlugin 예제:
   - 파라미터를 받아 처리
   - 검증 로직 포함
   
3. AsyncPlugin 예제:
   - 비동기 처리 (외부 API 호출)
   - httpx 사용
   
4. StatefulPlugin 예제:
   - 상태를 유지하는 플러그인
   - 카운터, 캐시 등

각 예제마다:
- 클래스 정의
- 등록 방법
- 테스트 코드
- 주석으로 설명

실행 가능한 스크립트로 만들어서 
바로 테스트할 수 있게 해줘.
```

### 6단계: 플러그인 로더 구현

#### 📌 목표
외부 Python 파일에서 플러그인을 동적으로 로드하는 기능을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/plugins/loader.py` 생성 후:**

```
플러그인을 동적으로 로드하는 PluginLoader를 만들어줘.

요구사항:
- 클래스명: PluginLoader
- 메서드:
  1. load_from_file(filepath: str) -> BasePlugin:
     - Python 파일에서 플러그인 클래스 로드
     - importlib 사용
     - 클래스가 BasePlugin 상속했는지 검증
     
  2. load_from_directory(dirpath: str) -> list[BasePlugin]:
     - 디렉토리의 모든 .py 파일 스캔
     - 플러그인 클래스 자동 탐색
     - 중복 이름 처리
     
  3. load_from_package(package_name: str) -> list[BasePlugin]:
     - 설치된 패키지에서 로드
     - entry point 사용
     
  4. validate_plugin(plugin_class: type) -> bool:
     - 플러그인 클래스 검증
     - 필수 메서드 구현 확인
     - 스키마 유효성 검사

- 안전한 로딩 (잘못된 코드로부터 보호)
- 로딩 실패 시 로그만 남기고 계속 진행
- 순환 import 방지
- 타입 힌트와 docstring

inspect 모듈로 클래스 검사 로직 구현해줘.
```

## 🎓 학습 정리

### 이 단계에서 배운 프롬프트 작성 기법

1. **플러그인 아키텍처**: 확장 가능한 시스템 설계 요청
2. **추상화와 인터페이스**: 다형성 활용 명시
3. **동적 로딩**: 런타임 코드 로딩 구현
4. **상태 관리**: 영속성과 동시성 고려

### 체크리스트 ✅

다음 파일들이 생성되었는지 확인하세요:

- [ ] `src/agent/plugins/base.py` - 플러그인 기반 클래스
- [ ] `src/agent/plugins/web_search.py` - 웹 검색 플러그인
- [ ] `src/agent/plugins/calculator.py` - 계산기 플러그인
- [ ] `src/agent/plugins/weather.py` - 날씨 플러그인
- [ ] `src/agent/plugins/loader.py` - 플러그인 로더
- [ ] `src/agent/state_manager.py` - 상태 관리자
- [ ] `src/agent/storage/base.py` - 저장소 인터페이스
- [ ] `examples/advanced_agent.py` - 고급 Agent 예제
- [ ] `examples/plugin_development.py` - 플러그인 개발 가이드

### 확인 명령어

```bash
# 고급 Agent 실행
uv run python examples/advanced_agent.py

# 플러그인 개발 가이드 실행
uv run python examples/plugin_development.py

# 플러그인 테스트
uv run pytest tests/plugins/

# 타입 체크
uv run mypy src/agent/plugins/
```

## 🔄 다음 단계

커스텀 기능 추가가 완료되었습니다!

👉 [Step 05: 테스트 및 배포](../step-05/README.md)로 이동하여 프로젝트를 완성해봅시다.

## 💡 심화 프롬프트

### 플러그인 마켓플레이스

```
플러그인 마켓플레이스 시스템을 만들어줘.

기능:
1. PluginRegistry 클래스:
   - 원격 저장소에서 플러그인 목록 가져오기
   - 플러그인 검색 (이름, 태그, 설명)
   - 플러그인 다운로드 및 설치
   - 버전 관리
   - 의존성 해결
   
2. 메타데이터:
   - plugin.json: 플러그인 정보
   - 작성자, 라이선스, 의존성 등
   
3. 보안:
   - 서명 검증
   - 샌드박스 실행

GitHub Releases를 마켓플레이스로 사용해줘.
```

### 플러그인 체인

```
여러 플러그인을 연결해서 실행하는 체인 시스템을 만들어줘.

기능:
- PluginChain 클래스
- 플러그인 순서대로 실행
- 이전 플러그인 출력을 다음 입력으로
- 조건부 실행 (if-then-else)
- 병렬 실행
- 에러 핸들링 (재시도, 폴백)

YAML로 체인 정의할 수 있게 해줘.
```

### 플러그인 모니터링

```
플러그인 실행을 모니터링하는 시스템을 추가해줘.

메트릭:
- 실행 횟수
- 평균 실행 시간
- 성공/실패율
- 리소스 사용량

기능:
- PluginMetrics 클래스
- 통계 수집
- 대시보드 (웹 UI)
- 알림 (임계값 초과 시)

Prometheus 형식으로 메트릭 export해줘.
```

---

**훌륭합니다! 🎉 거의 다 왔습니다! 마지막 단계로 가세요!**
