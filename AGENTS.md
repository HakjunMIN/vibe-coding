# AGENTS.md - AI 코딩 에이전트 작업 지시문

이 문서는 GitHub Copilot과 다른 AI 코딩 에이전트가 이 리포지토리를 점검하고 유지보수할 때 따라야 하는 기준입니다. 모든 작업 전에 이 문서와 `.github/copilot-instructions.md`를 먼저 읽습니다.

수강생은 이 문서가 아니라 [README.md](README.md)부터 읽습니다.

## 1. 리포 규칙

- 이 리포지토리는 GitHub Copilot으로 Microsoft Agent Framework 기반 Python Agent를 만드는 한국어 클릭스루형 워크샵입니다.
- API 키, 실제 endpoint, 토큰, 구독 ID, 개인 리소스 이름을 커밋하지 않습니다. `.env`에는 실제 값을 두고, `.env.example`과 문서에는 `<your-...>` placeholder만 씁니다.
- `LICENSE`는 코드의 MIT 라이선스, `LICENSE-DOCS`는 문서의 CC BY-SA 4.0 라이선스입니다. 두 파일을 임의로 변경하거나 삭제하지 않습니다.
- 새 파일과 폴더 이름은 공백과 비ASCII 문자를 쓰지 않고 kebab-case 영문으로 작성합니다. 랩 폴더는 `01-lab-name`, 단계 파일은 `01-step-name.md` 형식을 사용합니다.
- 루트 README의 전체 frontmatter와 랩 README의 축약 frontmatter를 유지합니다. 내용을 수정하면 `last_updated`를 갱신하고, `validated_on`은 실제 E2E 검증을 마친 사람이 기입합니다.
- 본문 실습 절차와 설명의 사실관계를 임의로 추가하거나 삭제하지 않습니다. 구조를 바꿀 때도 원문을 이동하거나 제목과 링크를 정리하는 범위에 머뭅니다.
- `main`에 직접 커밋하거나 push하지 않습니다. 작업 브랜치에서 논리적인 단위로 커밋한 뒤 PR로 검토받습니다.
- 외부 데이터셋과 서비스를 저장소에 복사하지 않습니다. 접근 조건, 라이선스, 크기, fallback을 문서에 기록합니다.
- 모든 `.ipynb`는 code cell의 `outputs`를 빈 배열로, `execution_count`를 `null`로 유지합니다. 실행 결과는 저장소 밖 임시 경로에 기록합니다.

## 2. 콘텐츠·노트북 스타일 가이드

문서 설명은 한국어로 작성하고, 기술 용어는 국내 실무에서 통용되는 영문 표기를 사용합니다. 코드, 식별자, 환경 변수, 파일명은 영어로 씁니다. 코드 주석은 코드만으로 이유를 알기 어려울 때만 짧게 추가합니다.

각 랩 README는 다음 순서를 유지합니다.

1. 축약 frontmatter: `title`, `duration_minutes`, `last_updated`
2. 개요와 학습 목표
3. 사전 요구사항
4. 소요 시간
5. 실습 단계
6. 검증
7. 정리 (Clean-up)
8. 트러블슈팅
9. 이전/다음 링크

원문에 소요 시간이나 정리 절차의 근거가 없으면 `<!-- TODO: 저자 작성 -->`으로 남깁니다. 새로운 사실을 추정해서 채우지 않습니다. 첫 랩의 이전 링크는 워크샵 홈, 마지막 랩의 다음 링크는 워크샵 홈이나 완료 안내를 가리켜야 합니다.

현재 저장소에는 노트북이 없습니다. 이후 노트북을 추가한다면 관련 단계 문서와 같은 번호 접두어를 사용하고, 해당 랩 README에 노트북 목록과 검증 방법을 기록합니다. markdown cell은 한국어, code cell의 식별자는 영어로 작성하며 모든 출력은 커밋 전에 제거합니다.

## 3. 검증 하네스

하네스는 devcontainer의 Bash를 기준으로 실행합니다. 최소 버전은 gitleaks 8.19와 Python 3.10입니다. Windows 로컬에서는 준비 작업에 PowerShell을 사용할 수 있지만, 아래 검사는 devcontainer 또는 Git Bash에서 실행합니다.

```bash
# (1) 시크릿 스캔 — 이력 포함 (gitleaks >= 8.19 신문법)
gitleaks git . --log-opts="--all" || { echo "FAIL: secrets"; exit 1; }

# (2) 개인 리소스 식별자 스캔 — 문서·코드·설정
grep -rEn --include='*.md' --include='*.py' --include='*.ipynb' --include='*.sh' --include='*.bicep' --include='*.json' \
  'https?://[a-z0-9-]+\.(openai\.azure\.com|cognitiveservices\.azure\.com|services\.ai\.azure\.com|azure-api\.net)' . \
  | grep -v '<your\|example\|placeholder' && echo "FAIL: personal endpoints" || echo "PASS"

# (3) 노트북 출력 클리어 확인
python3 - <<'EOF'
import json, glob, sys
bad = [f for f in glob.glob('**/*.ipynb', recursive=True)
       if any(c.get('outputs') or c.get('execution_count') is not None
              for c in json.load(open(f))['cells'] if c['cell_type']=='code')]
print("FAIL: outputs in", bad) if bad else print("PASS: notebooks clean")
sys.exit(1 if bad else 0)
EOF

# (4) 공백·비ASCII 경로 잔존 확인
find . -path ./.git -prune -o -print | grep -P '[ ]|[^\x00-\x7F]' \
  && echo "FAIL: non-standard paths" || echo "PASS"

# (5) frontmatter 스키마 검증
python3 - <<'EOF'
import re, sys, yaml
txt = open('README.md', encoding='utf-8').read()
m = re.match(r'^---\n(.*?)\n---', txt, re.S)
assert m, "FAIL: no frontmatter"
fm = yaml.safe_load(m.group(1))
required = ['type','title','description','level','authors','contacts','duration_minutes',
            'tags','language','execution','status','source','last_updated']
missing = [k for k in required if k not in fm]
if 'validated_on' not in fm: missing.append('validated_on(키 필수, 값은 공란 허용)')
print("FAIL: missing", missing) if missing else print("PASS: frontmatter")
sys.exit(1 if missing else 0)
EOF

# (6) 깨진 상대 링크·이미지 참조 검사 (fenced/inline 코드 제외, <img src> 포함)
python3 - <<'EOF'
import re, glob, os, sys, urllib.parse
bad = []
for f in glob.glob('**/*.md', recursive=True):
    t = open(f, encoding='utf-8').read()
    t = re.sub(r'```.*?```', '', t, flags=re.S)   # fenced code block 제외 (SQL 등 오인 방지)
    t = re.sub(r'`[^`\n]*`', '', t)               # inline code 제외
    base = os.path.dirname(f)
    links = re.findall(r'\]\(([^)#\s]+?)(?:#[^)]*)?\)', t)
    links += re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', t)
    for link in links:
        if link.startswith(('http', 'mailto:', 'data:')): continue
        p = os.path.normpath(os.path.join(base, urllib.parse.unquote(link.strip())))
        if not os.path.exists(p): bad.append(f"{f} -> {link}")
print("FAIL:\n" + "\n".join(bad)) if bad else print("PASS: links")
sys.exit(1 if bad else 0)
EOF

# (7) 랩 README 축약 frontmatter 검사 (title·duration_minutes·last_updated 키 존재)
python3 - <<'EOF'
import re, glob, os, sys, yaml
bad = []
for f in glob.glob('**/README.md', recursive=True):
    d = os.path.basename(os.path.dirname(f))
    if not re.match(r'^(\d{2}-|lab\d)', d): continue
    m = re.match(r'^---\n(.*?)\n---', open(f, encoding='utf-8').read(), re.S)
    if not m: bad.append(f + ' -> frontmatter 없음'); continue
    try: fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e: bad.append(f + ' -> YAML 파싱 오류(따옴표 누락 등)'); continue
    miss = [k for k in ('title','duration_minutes','last_updated') if k not in fm]
    if miss: bad.append(f + ' -> 키 누락: ' + ','.join(miss))
print("FAIL:\n" + "\n".join(bad)) if bad else print("PASS: lab frontmatter")
sys.exit(1 if bad else 0)
EOF

# (8) 이미지 alt-text 검사 (빈 alt 금지 — markdown ![]와 HTML <img>)
python3 - <<'EOF'
import re, glob, sys
bad = []
for f in glob.glob('**/*.md', recursive=True):
    t = re.sub(r'```.*?```', '', open(f, encoding='utf-8').read(), flags=re.S)
    if re.search(r'!\[\s*\]\(', t): bad.append(f + ' -> 빈 alt (markdown)')
    for img in re.findall(r'<img[^>]*>', t):
        m = re.search(r'alt=["\']([^"\']*)["\']', img)
        if not m or not m.group(1).strip(): bad.append(f + ' -> 빈 alt (<img>)')
print("FAIL:\n" + "\n".join(bad)) if bad else print("PASS: alt-text")
sys.exit(1 if bad else 0)
EOF

# (9) 랩 전용 자산 교차 참조 검사 (다른 랩의 assets/ 참조 = shared-assets 이동 대상)
python3 - <<'EOF'
import re, glob, os, sys, urllib.parse
bad = []
for f in glob.glob('**/*.md', recursive=True):
    t = re.sub(r'```.*?```', '', open(f, encoding='utf-8').read(), flags=re.S)
    base = os.path.dirname(f).replace(os.sep, '/')
    links = re.findall(r'\]\(([^)#\s]+?)\)', t) + re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', t)
    for l in links:
        if l.startswith(('http','mailto:','data:')) or '/assets/' not in l or 'shared-assets' in l: continue
        p = os.path.normpath(os.path.join(base, urllib.parse.unquote(l))).replace(os.sep, '/')
        owner = p.split('/assets/')[0]
        if not (base + '/').startswith(owner + '/'):
            bad.append(f + ' -> ' + l + ' (shared-assets 이동 대상)')
print("FAIL:\n" + "\n".join(bad)) if bad else print("PASS: assets")
sys.exit(1 if bad else 0)
EOF
```

검사 하나라도 실패하면 원인을 수정하고 같은 검사를 다시 실행합니다. 검사 항목을 삭제하거나 결과를 무시하지 않습니다.

## 4. 백로그·DO NOT

### 백로그

- 5개 랩의 `duration_minutes`를 저자가 확정합니다.
- 5개 랩의 정리(Clean-up) 절차를 비용과 리소스 삭제 기준에 맞춰 저자가 작성합니다.
- Step 02부터 Step 05까지의 트러블슈팅을 실제 실행 결과에 근거해 작성합니다.
- AutoGen 표기와 Microsoft Agent Framework SDK 설명의 정합성을 별도 콘텐츠 검토에서 확인합니다.
- E2E 검증을 마친 뒤 루트 README의 `validated_on`을 검증한 사람이 기입합니다.

### DO NOT

- DO NOT: 하네스 (1)·(2)에서 노출이 발견된 상태로 커밋하거나 push합니다.
- DO NOT: `main`에 직접 push합니다.
- DO NOT: 본문 실습 절차, 설명문, 코드 동작을 근거 없이 추가·삭제·요약합니다.
- DO NOT: E2E 실행 없이 `validated_on`을 기입합니다.
- DO NOT: 확정되지 않은 경로를 삭제하거나 랩을 분할·병합합니다.
- DO NOT: 외부 데이터셋과 서비스를 저장소에 복사합니다.
- DO NOT: 하네스 검사 항목을 수정하거나 건너뜁니다.