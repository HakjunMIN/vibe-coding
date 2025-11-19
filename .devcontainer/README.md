# Dev Container 설정

이 프로젝트는 GitHub Codespaces 및 VS Code Dev Containers를 지원합니다.

## 포함된 구성

- **Python 3.12**: 프로젝트 요구사항에 맞는 Python 버전
- **uv**: 빠른 Python 패키지 관리자 (자동 설치)
- **VS Code 확장**:
  - Python 지원 (Pylance, Black formatter)
  - Ruff (린터 및 포매터)
  - GitHub Copilot (코딩 어시스턴트)

## 사용 방법

### GitHub Codespaces

1. GitHub 리포지토리 페이지에서 `Code` 버튼 클릭
2. `Codespaces` 탭 선택
3. `Create codespace on main` 클릭

### VS Code Dev Containers (로컬)

1. VS Code에 "Dev Containers" 확장 설치
2. 프로젝트 폴더 열기
3. `F1` → "Dev Containers: Reopen in Container" 선택

## 자동 설정

컨테이너 생성 시 자동으로:
- uv가 설치됩니다
- `uv sync --all-extras`로 모든 의존성이 설치됩니다
- 가상환경이 `.venv`에 생성됩니다
- VS Code가 자동으로 해당 Python 인터프리터를 사용합니다
