# Step 05: 테스트 및 배포

## 🎯 학습 목표

이 마지막 단계에서는 AI Agent를 테스트하고, 문서화하고, 배포하는 방법을 배웁니다. 프로덕션 레벨의 코드 품질을 위한 프롬프트 작성법을 익힙니다.

## 📝 이 단계에서 배울 내용

- 포괄적인 테스트 코드 생성 프롬프트
- 문서 자동화 요청 방법
- CI/CD 파이프라인 구성
- 배포 설정 파일 생성

## 🚀 시작하기

### 1단계: 유닛 테스트 작성

#### 📌 목표
모든 주요 컴포넌트에 대한 유닛 테스트를 작성합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `tests/conftest.py` 생성 후 Copilot Chat:**

```
pytest를 위한 공통 fixture를 정의하는 conftest.py를 만들어줘.

필요한 fixture:
1. mock_config: 테스트용 AgentConfig 객체
   - 실제 API 키 대신 더미 값 사용
   - 모든 필수 필드 포함
   
2. mock_llm_response: LLM 응답 mock
   - httpx나 openai 라이브러리 mock
   - 다양한 응답 패턴 지원
   
3. temp_storage: 임시 저장소
   - 테스트용 임시 디렉토리
   - 테스트 후 자동 정리
   
4. sample_messages: 테스트용 메시지 리스트
   - 다양한 시나리오 커버
   
5. plugin_manager: 테스트용 PluginManager
   - 실제 플러그인 없이 mock 플러그인 사용

pytest-mock과 pytest-asyncio 사용.
각 fixture에 scope와 docstring 추가.
```

#### 💡 프롬프트 작성 팁

- **Mock 전략 명시**: 어떤 외부 의존성을 mock할지
- **Fixture 범위**: session, module, function 등
- **자동 정리**: teardown 로직 포함
- **재사용성**: 여러 테스트에서 사용 가능하게

**파일: `tests/test_agent_config.py` 생성 후:**

```
AgentConfig 클래스를 위한 포괄적인 테스트를 작성해줘.

테스트 케이스:
1. test_valid_config_creation: 정상 생성
2. test_default_values: 기본값 검증
3. test_temperature_validation: temperature 범위 검증
   - 정상 범위 (0.0, 0.7, 2.0)
   - 범위 초과 (음수, 2.0 초과)
4. test_max_tokens_validation: max_tokens 검증
5. test_api_key_required: API 키 필수 검증
6. test_from_env: 환경 변수 로드 테스트
   - monkeypatch로 환경 변수 설정
7. test_secret_str_masking: API 키 마스킹 확인

pytest 사용:
- 파라미터화된 테스트 (@pytest.mark.parametrize)
- 예외 테스트 (pytest.raises)
- 명확한 테스트 이름과 docstring
- given-when-then 주석 구조

각 테스트는 독립적으로 실행 가능해야 해.
```

**파일: `tests/test_conversation_agent.py` 생성 후:**

```
ConversationAgent를 위한 테스트를 작성해줘.

테스트 케이스:
1. test_agent_initialization: Agent 초기화
2. test_chat_basic: 기본 대화
   - LLM 응답 mock
   - 응답 형식 검증
3. test_chat_with_context: 컨텍스트 유지 확인
4. test_chat_error_handling: 에러 처리
   - API 실패
   - 타임아웃
5. test_reset_conversation: 대화 초기화
6. test_save_load_conversation: 저장/로드
7. test_streaming_response: 스트리밍 테스트

Mock 사용:
- ResponseGenerator mock
- ContextManager mock  
- MessageProcessor mock

pytest-asyncio로 비동기 테스트도 포함.
커버리지 높게 작성해줘.
```

### 2단계: 통합 테스트 작성

#### 📌 목표
여러 컴포넌트가 함께 작동하는지 테스트합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `tests/integration/test_plugin_integration.py` 생성 후:**

```
플러그인 통합 테스트를 작성해줘.

시나리오:
1. test_plugin_registration_and_execution:
   - 플러그인 등록
   - Agent에서 플러그인 실행
   - 결과 검증
   
2. test_multiple_plugins:
   - 여러 플러그인 동시 등록
   - 올바른 플러그인 선택
   
3. test_plugin_error_isolation:
   - 한 플러그인 실패 시 다른 플러그인은 정상 작동
   
4. test_function_calling_flow:
   - LLM이 플러그인 호출
   - 결과를 다시 LLM에 전달
   - 최종 응답 생성

실제 플러그인 사용 (Calculator 등):
- 외부 API 호출 없는 플러그인만
- 또는 mock 서버 사용

통합 테스트는 느릴 수 있으니 
@pytest.mark.integration으로 마킹해줘.
```

**파일: `tests/integration/test_end_to_end.py` 생성 후:**

```
전체 시스템의 end-to-end 테스트를 작성해줘.

시나리오:
1. test_complete_conversation_flow:
   - Agent 생성 (from_env)
   - 여러 메시지 주고받기
   - 상태 저장
   - Agent 재생성
   - 상태 로드
   - 대화 이어가기
   
2. test_plugin_based_conversation:
   - 계산 요청
   - 플러그인 자동 실행
   - 결과 포함한 응답
   
3. test_session_management:
   - 세션 생성
   - 여러 대화
   - 세션 조회
   - 세션 삭제

docker-compose로 필요한 서비스 띄우기:
- Redis (상태 저장용)
- 테스트 DB

@pytest.mark.e2e로 마킹.
실행 시간 오래 걸려도 괜찮아.
```

### 3단계: 성능 및 부하 테스트

#### 📌 목표
Agent의 성능을 측정하고 병목 지점을 찾습니다.

#### ✍️ 프롬프트 작성 예시

**파일: `tests/performance/test_performance.py` 생성 후:**

```
성능 테스트를 작성해줘.

테스트:
1. test_response_time:
   - 단일 메시지 처리 시간 측정
   - 평균, 최소, 최대, 백분위수 (p50, p95, p99)
   - 임계값 검증 (예: 95%가 2초 이내)
   
2. test_throughput:
   - 초당 처리 가능한 메시지 수
   - 병렬 요청 테스트
   
3. test_memory_usage:
   - 메모리 누수 검사
   - 장시간 실행 시 메모리 증가 추적
   
4. test_concurrent_sessions:
   - 동시 세션 처리
   - 100개 이상 세션 테스트

pytest-benchmark 사용:
- @pytest.mark.benchmark 데코레이터
- 벤치마크 결과 자동 저장
- 이전 결과와 비교

psutil로 리소스 모니터링.
결과를 JSON으로 export.
```

**파일: `tests/performance/locustfile.py` 생성 후:**

```
Locust를 사용한 부하 테스트 스크립트를 작성해줘.

시나리오:
- Agent API 엔드포인트 호출
- 다양한 메시지 패턴
- 플러그인 사용 포함

Locust 태스크:
1. send_simple_message: 간단한 메시지
2. send_complex_message: 긴 메시지
3. use_plugin: 플러그인 요청
4. stream_response: 스트리밍 응답

설정:
- 점진적 사용자 증가 (0 -> 100)
- 랜덤 대기 시간
- 에러율 추적

실행 방법과 결과 해석을 주석으로 포함해줘.
```

### 4단계: 문서 자동화

#### 📌 목표
코드 문서화를 자동화합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `docs/conf.py` 생성 후:**

```
Sphinx 문서화를 위한 conf.py를 작성해줘.

설정:
- 프로젝트: Vibe Coding AI Agent
- 테마: sphinx-rtd-theme (Read the Docs)
- 확장:
  - sphinx.ext.autodoc: 자동 API 문서
  - sphinx.ext.napoleon: Google/NumPy docstring
  - sphinx.ext.viewcode: 소스 코드 링크
  - sphinx.ext.intersphinx: 외부 문서 링크
  - myst_parser: Markdown 지원

autodoc 설정:
- 타입 힌트 표시
- private 멤버 제외
- 상속 멤버 포함

intersphinx_mapping:
- Python 표준 라이브러리
- Pydantic
- httpx

HTML 테마 커스터마이징.
```

**파일: `docs/api/index.rst` 생성 후:**

```
API 문서 인덱스를 작성해줘.

구조:
1. Agent 모듈
   - base_agent
   - conversation_agent
   - factory
   
2. Config 모듈
   - agent_config
   
3. Plugins 모듈
   - base
   - 각 플러그인
   
4. Utils 모듈
   - logger
   - validators

각 모듈마다:
- automodule 지시문
- members, undoc-members 옵션
- 예제 코드 포함

reStructuredText 형식으로.
TOC tree 구조화.
```

**프롬프트로 README 업데이트:**

```
프로젝트 루트의 README.md를 업데이트해줘.

추가할 섹션:
1. 배지: 
   - Python 버전
   - 테스트 상태
   - 커버리지
   - 라이선스
   
2. 기능 목록:
   - 완성된 모든 기능 나열
   - 각 플러그인 설명
   
3. 빠른 시작:
   - 설치 명령어
   - 최소 예제 코드
   - 실행 결과
   
4. 문서 링크:
   - 전체 문서
   - API 레퍼런스
   - 튜토리얼
   
5. 개발자 가이드:
   - 기여 방법
   - 테스트 실행
   - 플러그인 개발

기존 내용은 유지하되, 완성된 프로젝트에 맞게 수정해줘.
```

### 5단계: CI/CD 파이프라인

#### 📌 목표
자동화된 테스트와 배포 파이프라인을 구성합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `.github/workflows/test.yml` 생성 후:**

```
GitHub Actions를 사용한 CI 파이프라인을 작성해줘.

워크플로우: Test
트리거: push, pull_request (main, develop 브랜치)

Jobs:
1. lint:
   - black으로 포매팅 체크
   - ruff로 린팅
   - mypy로 타입 체크
   
2. test:
   - 매트릭스: Python 3.11, 3.12
   - OS: ubuntu-latest, macos-latest
   - 단계:
     - 코드 체크아웃
     - Python 설정 (uv 사용)
     - 의존성 설치
     - 유닛 테스트 (pytest)
     - 커버리지 측정 (pytest-cov)
     - 커버리지 업로드 (codecov)
     
3. integration-test:
   - docker-compose로 서비스 실행
   - 통합 테스트 실행
   - 로그 수집

캐싱 설정으로 빌드 속도 최적화.
실패 시 알림.
```

**파일: `.github/workflows/publish.yml` 생성 후:**

```
PyPI 배포를 위한 CD 파이프라인을 작성해줘.

워크플로우: Publish
트리거: 
- push (tags: v*)
- workflow_dispatch (수동 실행)

Jobs:
1. build:
   - 패키지 빌드 (uv build)
   - wheel과 sdist 생성
   - artifact 업로드
   
2. test-publish:
   - TestPyPI에 업로드
   - 설치 테스트
   
3. publish:
   - test-publish 성공 시만 실행
   - PyPI에 업로드
   - GitHub Release 생성
   - 릴리스 노트 자동 생성

Secrets 사용:
- PYPI_TOKEN
- GITHUB_TOKEN

권한 설정 포함.
```

**파일: `.github/workflows/docs.yml` 생성 후:**

```
문서 배포 워크플로우를 작성해줘.

워크플로우: Deploy Docs
트리거: push (main 브랜치), workflow_dispatch

Jobs:
1. build-docs:
   - Sphinx로 HTML 생성
   - API 문서 자동 생성
   
2. deploy:
   - GitHub Pages에 배포
   - 또는 Read the Docs 트리거

문서 버전 관리:
- latest (main 브랜치)
- stable (최신 릴리스)
- 각 버전별 문서 보관
```

### 6단계: 배포 설정

#### 📌 목표
다양한 환경에 배포하기 위한 설정 파일을 만듭니다.

#### ✍️ 프롬프트 작성 예시

**파일: `Dockerfile` 생성 후:**

```
AI Agent를 위한 프로덕션 Dockerfile을 작성해줘.

요구사항:
- 베이스 이미지: python:3.11-slim
- 멀티 스테이지 빌드:
  - builder: 의존성 설치
  - runtime: 실행 환경
- uv 사용해서 의존성 설치
- 비 root 유저로 실행
- 헬스체크 포함
- 최적화:
  - .dockerignore 활용
  - 레이어 캐싱
  - 이미지 크기 최소화

ENTRYPOINT와 CMD 설정.
환경 변수 설정 가이드 주석 포함.
```

**파일: `docker-compose.yml` 생성 후:**

```
Agent와 필요한 서비스를 위한 docker-compose.yml을 작성해줘.

서비스:
1. agent:
   - Dockerfile로 빌드
   - 환경 변수 (.env 파일)
   - 볼륨 (데이터 영속성)
   - 포트 노출
   
2. redis (선택):
   - 상태 저장용
   - 볼륨 마운트
   
3. postgres (선택):
   - 대화 기록 저장
   - 초기화 스크립트

네트워크 설정.
헬스체크와 재시작 정책.
프로덕션과 개발 환경 분리 (profiles).
```

**파일: `kubernetes/deployment.yaml` 생성 후:**

```
Kubernetes 배포를 위한 매니페스트를 작성해줘.

리소스:
1. Deployment:
   - Agent 파드
   - 레플리카: 3
   - 리소스 제한 (CPU, 메모리)
   - 롤링 업데이트 전략
   - 환경 변수 (ConfigMap, Secret)
   
2. Service:
   - LoadBalancer 타입
   - 포트 매핑
   
3. ConfigMap:
   - Agent 설정
   
4. Secret:
   - API 키
   
5. HorizontalPodAutoscaler:
   - CPU 기반 오토스케일링

모범 사례:
- 헬스체크 (liveness, readiness)
- 리소스 쿼터
- 네임스페이스 분리
```

### 7단계: 모니터링 및 로깅

#### 📌 목표
프로덕션 환경에서 Agent를 모니터링합니다.

#### ✍️ 프롬프트 작성 예시

**파일: `src/agent/observability.py` 생성 후:**

```
Agent 관측성을 위한 모듈을 만들어줘.

기능:
1. MetricsCollector 클래스:
   - 메트릭 수집 (Prometheus 형식)
   - 카운터: 요청 수, 에러 수
   - 히스토그램: 응답 시간, 토큰 수
   - 게이지: 활성 세션 수
   
2. TracingManager 클래스:
   - 분산 추적 (OpenTelemetry)
   - 스팬 생성 및 전파
   - 컨텍스트 관리
   
3. StructuredLogger 클래스:
   - JSON 로깅
   - 필드: timestamp, level, message, trace_id, user_id 등
   - 민감 정보 마스킹
   
4. HealthCheck 클래스:
   - /health 엔드포인트 응답
   - 의존성 체크 (DB, Redis 등)
   - 상태: healthy, degraded, unhealthy

데코레이터로 함수에 쉽게 적용할 수 있게.
비동기 지원.
```

**파일: `prometheus.yml` 생성 후:**

```
Prometheus 설정 파일을 작성해줘.

스크랩 설정:
- Agent 메트릭 엔드포인트
- 간격: 15초
- 타임아웃: 10초

알림 규칙:
- 에러율 > 5%
- 응답 시간 p95 > 3초
- 메모리 사용률 > 80%

Alertmanager 통합.
```

## 🎓 학습 정리

### 이 단계에서 배운 프롬프트 작성 기법

1. **테스트 전략**: 유닛, 통합, E2E 테스트 구분
2. **인프라 as 코드**: 배포 설정을 코드로 관리
3. **CI/CD 파이프라인**: 자동화된 테스트와 배포
4. **관측성**: 모니터링, 로깅, 추적

### 최종 체크리스트 ✅

테스트:
- [ ] `tests/conftest.py` - 공통 fixture
- [ ] `tests/test_*.py` - 유닛 테스트
- [ ] `tests/integration/` - 통합 테스트
- [ ] `tests/performance/` - 성능 테스트

문서:
- [ ] `docs/conf.py` - Sphinx 설정
- [ ] `docs/api/` - API 문서
- [ ] 업데이트된 `README.md`

CI/CD:
- [ ] `.github/workflows/test.yml` - CI
- [ ] `.github/workflows/publish.yml` - CD
- [ ] `.github/workflows/docs.yml` - 문서 배포

배포:
- [ ] `Dockerfile` - 컨테이너 이미지
- [ ] `docker-compose.yml` - 로컬 환경
- [ ] `kubernetes/` - K8s 매니페스트

모니터링:
- [ ] `src/agent/observability.py` - 관측성
- [ ] `prometheus.yml` - 메트릭 수집

### 확인 명령어

```bash
# 모든 테스트 실행
uv run pytest tests/ -v --cov=src

# 커버리지 리포트
uv run pytest --cov=src --cov-report=html

# 린팅 및 포매팅
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# 문서 빌드
cd docs && make html

# Docker 이미지 빌드
docker build -t vibe-coding-agent .

# Docker Compose 실행
docker-compose up -d

# 성능 테스트
uv run pytest tests/performance/ -v
```

## 🎉 프로젝트 완성!

축하합니다! AI Agent 프로젝트가 완성되었습니다!

### 완성된 것들

✅ Microsoft Agent Framework 기반 AI Agent  
✅ 플러그인 시스템으로 확장 가능  
✅ 상태 관리 및 세션 저장  
✅ 포괄적인 테스트 커버리지  
✅ 자동화된 CI/CD 파이프라인  
✅ 프로덕션 배포 준비  
✅ 모니터링 및 관측성  

### 다음 단계 제안

1. **실제 사용 사례 구현**
   - 특정 도메인에 맞는 플러그인 개발
   - 커스텀 프롬프트 엔지니어링
   
2. **고급 기능 추가**
   - 멀티모달 지원 (이미지, 음성)
   - 멀티 에이전트 협업
   - 강화학습 기반 개선
   
3. **스케일링**
   - 분산 처리
   - 로드 밸런싱
   - 캐싱 최적화
   
4. **커뮤니티 기여**
   - 오픈소스 공개
   - 플러그인 마켓플레이스
   - 튜토리얼 및 블로그 작성

## 💡 프로젝트 개선 프롬프트

### 코드 품질 향상

```
전체 프로젝트를 리뷰하고 개선 사항을 제안해줘.

검토 항목:
- 코드 중복 제거
- 디자인 패턴 적용
- 에러 처리 개선
- 성능 최적화 포인트
- 보안 취약점

각 개선 사항마다 우선순위와 예상 영향 포함.
```

### 문서 개선

```
사용자 가이드를 작성해줘.

대상: 비개발자도 이해할 수 있게
내용:
- Agent가 무엇을 할 수 있는지
- 사용 시나리오별 가이드
- 자주 묻는 질문 (FAQ)
- 트러블슈팅

스크린샷과 다이어그램 위치 표시.
```

### 릴리스 체크리스트

```
v1.0.0 릴리스를 위한 체크리스트를 만들어줘.

항목:
- 기능 완성도
- 테스트 커버리지 목표 (>90%)
- 문서 완성도
- 성능 벤치마크
- 보안 감사
- 라이선스 검토
- 릴리스 노트 작성

각 항목의 완료 기준 포함.
```

## 📚 학습 리소스

### 추가 학습 자료

- [GitHub Copilot 고급 가이드](https://docs.github.com/en/copilot)
- [Microsoft Autogen 문서](https://microsoft.github.io/autogen/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Python 모범 사례](https://docs.python-guide.org/)

### 커뮤니티

- GitHub Discussions에서 질문하기
- Discord 커뮤니티 참여
- 블로그에 경험 공유

---

**🎊 축하합니다! Vibe Coding 마스터가 되셨습니다! 🎊**

이제 프롬프트만으로 복잡한 AI Agent를 만드는 방법을 완전히 이해했습니다.
배운 기술을 활용해서 더 멋진 프로젝트를 만들어보세요!

**Keep Vibing! 🎵✨**
