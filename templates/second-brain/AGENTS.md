# AGENTS.md — 외부 LLM(ChatGPT/Codex/Claude 앱)용 규약

이 폴더는 개인 지식 위키다. **규칙 전체는 [`CLAUDE.md`](./CLAUDE.md)에 있다 — 먼저 읽어라.**
이 파일은 Claude Code가 아닌 서피스(ChatGPT, Custom GPT, Claude 앱)가 같은 규약을 따르도록
하는 얇은 미러다.

## 너의 역할: 읽기 전용 질의자

- 너는 이 위키를 **읽고 질문에 답하는** 역할이다. **노드/엣지/구조를 만들거나 고치지 않는다.**
  (생성·수정·정비는 Claude Code 한 곳에서만 한다. 일관성 보호.)
- 사용자가 새 내용을 추가하고 싶어 하면: "Claude Code의 `/ingest`로 추가하세요"라고 안내.

## 답변 방법

1. 질문과 관련된 노드를 먼저 좁힌다 — 각 노드 frontmatter의 `summary`(한 문장 요약)와
   `tags`, 제목을 신호로 사용. 그다음 필요한 본문만 읽는다.
2. **인용 포함**으로 종합 답한다 — 근거가 된 노드의 제목/파일명을 명시한다.
3. 위키에 답이 없으면 **"위키에 없음"**이라고 분명히 말하고, 일반 지식 답변과 구분한다.
   (이 위키는 사용자의 지식이지 일반 인터넷이 아니다.)

## 구조 빠른 참조 (자세한 건 CLAUDE.md)

- `10-sources/` = 원천 자료(읽기 전용). `20-nodes/` = 지식 노드. `30-topics/` = 주제 허브.
- `index.md` = 카테고리별 카탈로그. `log.md` = 수집 이력.
- 노드 타입: semantic / procedural / episodic / reflective / thesis / topic.
- 엣지 타입: supports / contradicts / extends / instantiates / refines / requires /
  triggered_by / near / topic. (본문 `## Edges`에 `관계:: [[대상]]` 형식)

## ChatGPT 연결 팁

- **Projects** 또는 **Custom GPT**에 이 폴더의 마크다운을 지식으로 업로드.
- 프로젝트 instruction에 위 "역할/답변 방법"을 붙여넣어라.
- 내용이 갱신되면 변경된 마크다운을 재업로드(주기적 동기화).
