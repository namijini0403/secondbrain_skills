# secondbrain_skills — LLM이 관리하는 지식 위키 스타터

**소스만 넣으면 Claude Code가 지식 그래프를 만들어 주는** 세컨드 브레인/RAG 구축 키트입니다.
실제로 운영 중인 개인 지식위키·교육과정 지식그래프·학교앱 보안 설계에서 하네스(규칙서 +
스킬 + 서브에이전트)만 추출해 일반화했습니다. 선생님들이 바로 쓸 수 있게 만들었어요.

## 무엇이 들어있나

| 구성 | 폴더 | 용도 |
|------|------|------|
| **개인 second brain** | `templates/second-brain/` | 논문·연수자료·아이디어를 6타입 노드 + 9타입 엣지 지식그래프로. Obsidian 호환 |
| **교육과정 지식그래프** | `templates/curriculum-kb/` | 2022 개정 교육과정 성취기준을 "개념 원자"로 분해 — 선수학습 결손 추적용 |
| **연구용(논문) 하네스** | `templates/kg-research/` | 심사 방어 가능한 지식그래프 구축(불변 규칙·이중 코딩·품질 게이트) — 고급 |
| **문서 추출 스킬** | `skills/extract-documents/` | **HWP·HWPX·PDF·XLSX·DOCX → 텍스트**. 한국 학교 문서 대응 |
| **RAG 내보내기 스킬** | `skills/rag-export/` | 위키 → **AnythingLLM·Open WebUI·Khoj·LightRAG** 등 검증된 오픈소스 RAG 스택 연결 |
| **학교앱 보안 팩** | `security/` | 학생 데이터 다루는 앱의 보안·개인정보 설계 방법론 + 감사 에이전트 |

## 준비물

1. **[Claude Code](https://claude.com/claude-code)** 설치 + Claude 구독 (Pro면 충분)
2. **Python 3.9+** (HWP/PDF 추출용 — 없어도 위키 자체는 동작)
3. (선택) **[Obsidian](https://obsidian.md)** — 지식 그래프 시각화용. Dataview·Juggl 플러그인 권장

## 빠른 시작 (Windows)

```powershell
# 1. 이 저장소 받기 (git 없으면 GitHub에서 Code → Download ZIP)
git clone https://github.com/namijini0403/secondbrain_skills.git
cd secondbrain_skills

# 2. 원하는 위치에 설치 (예: 문서 폴더의 my-brain)
.\install.ps1 -Target "$HOME\Documents\my-brain"

# 3. (권장) 문서 추출 의존성
pip install olefile pypdf defusedxml

# 4. 소스 넣고 시작
#    my-brain\10-sources\ 에 PDF/HWP/메모 등을 넣은 뒤:
cd "$HOME\Documents\my-brain"
claude
```

Claude Code 안에서:
```
/setup            ← 첫 실행: 짧은 인터뷰로 프로필 생성 (이게 증류 기준이 됨)
/ingest 파일명    ← 소스를 노드로 분해해 위키에 연결
```

교육과정 그래프를 만들려면: `.\install.ps1 -Target "..." -Kind curriculum-kb`
macOS/Linux는 `./install.sh <대상폴더> [종류] [--with-security]`.

## 평소 사용법 (second brain)

| 커맨드 | 하는 일 | 주기 |
|--------|---------|------|
| `/ingest <소스>` | 소스 → 타입 노드 분해 + 엣지 연결 | 소스 생길 때 |
| `/review` | 인박스 비우기 + 이번 주 사건 기록 + 정비 | 주 1회 |
| `/distill` | 갓 만든 노드를 3질문(왜/긴장/적용)으로 증류 | 격주 |
| `/connect` | 노드 사이 누락된 논증 엣지 발굴 | 월 1회 |
| `/lint` | 깨진 링크·고아 노드·모순 건강검진 | 월 1회 |

그냥 질문하면 위키를 근거로 **인용 포함** 답변하고, 위키에 없으면 "없음"이라고 말합니다.
자세한 규칙은 각 템플릿의 `CLAUDE.md`(LLM용 규칙서 — 사람이 읽어도 됩니다)에 있습니다.

## 문서 추출 스킬 (단독 사용도 가능)

```bash
python skills/extract-documents/scripts/extract.py 공문.hwp 계획서.hwpx 자료.pdf 명렬.xlsx
# → 각 파일 옆에 *.extracted.md 생성
```
HWPX/XLSX/DOCX는 설치 없이 동작, HWP는 `pip install olefile`, PDF는 `pip install pypdf`.
암호 문서·배포용(DRM) HWP·스캔 PDF는 명확한 오류/경고로 안내합니다.

## 다른 RAG 앱에 연결하기 (`/export-rag`)

위키가 커지면 Claude Code 밖에서도 쓰고 싶어집니다. Claude Code에서 `/export-rag`를
실행하면 `rag-export/` 폴더에 3가지 범용 포맷이 생깁니다:

- `corpus.md` — **AnythingLLM**(데스크톱 앱, 제일 쉬움)·**Open WebUI**(교무실 공용 서버)·ChatGPT 프로젝트에 업로드
- `corpus.jsonl` — LlamaIndex·LangChain·**LightRAG** 같은 파이프라인용 (메타데이터 동봉)
- `graph.json` — 타입 엣지 그래프 (requires 결손 체인 등을 그래프 RAG에 주입)

어떤 도구를 고를지 판단 가이드와 도구별 연결 절차는
[`skills/rag-export/SKILL.md`](skills/rag-export/SKILL.md)에 있습니다.
원칙: 외부 도구는 **읽기 전용**(쓰기는 Claude Code만), `10-sources/` 원문은 업로드 금지.

## 학교앱 보안 팩 (선택)

앱을 만들어 학급에 배포하는 선생님용. `-WithSecurity`로 설치하면:
- `school-app-security` 스킬: 코드 전수조사 → 사실 브리프 → 문서 세트(동의서·처리방침·
  RBAC·보유파기 등) → 감사의 4단계 방법론 (ASVS L2 + 개인정보보호법 기준)
- `security-auditor` 에이전트: 읽기 전용 보안 감사 (발견 보고 → 수정은 분리)

## 자주 묻는 질문

**Q. 비용이 드나요?** — Claude 구독 외 추가 API 과금 0원이 설계 원칙입니다.
웹 검색 등 외부 호출은 하기 전에 물어보게 되어 있습니다.

**Q. 학생 개인정보를 넣어도 되나요?** — **넣지 마세요.** 이 위키는 지식 관리용입니다.
학생 실명·성적 등이 든 파일은 `10-sources/`에 넣기 전에 비식별 처리하고,
위키 폴더를 GitHub 등에 올릴 때는 반드시 내용물을 확인하세요.

**Q. 교육과정 원문 PDF를 GitHub에 올려도 되나요?** — 공개 레포에는 올리지 마세요
(저작권·용량). 원문은 로컬 `10-sources/`에만 두면 됩니다.

**Q. ChatGPT에서도 쓸 수 있나요?** — 읽기(질의)는 가능합니다. 각 템플릿의 `AGENTS.md`를
참고해 마크다운을 업로드하세요. **쓰기는 Claude Code 한 곳으로 단일화**가 규칙입니다.

## 구조 철학 (왜 이렇게 생겼나)

- **3계층**: 원천(`10-sources/`, 읽기 전용) / 위키(`20-nodes/`, LLM 소유) / 스키마(`CLAUDE.md`, 공동 진화)
- **한 노드 = 한 아이디어**, `summary` 한 문장 = 다른 LLM이 본문 안 읽고 관련성 판단하는 신호
- **타입 있는 엣지**(supports/contradicts/requires…)가 그래프의 가치 — 링크 수가 아니라 논증 사슬
- **위임 + 3-스트라이크**: 반복 작업은 작은 모델에, 판단은 큰 모델에, 실패 3회면 승격

## 라이선스

MIT — 자유롭게 쓰고 고치고 나누세요.
