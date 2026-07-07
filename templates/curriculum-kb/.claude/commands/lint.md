---
description: 교육과정 위키 건강 검진 — 고아/누락 requires/원문 불일치/깨진 링크 점검
---

`CLAUDE.md` §6 Lint 워크플로우를 따른다. 범위: $ARGUMENTS (없으면 위키 전체)

`20-nodes/`, `30-topics/`, `index.md`를 훑어 다음을 점검하고 **보고서**를 먼저 낸다:
- 고아 노드(엣지 0), 명백한 `requires` 누락(선수 체인 끊김)
- `aligns_to` 없는 concept/skill, `near`로 안 묶인 혼동쌍
- 중복 개념, 깨진 `[[링크]]`, `summary`/`source` 누락
- standard 노드 코드·문구가 원문과 불일치할 가능성(후보)
- `index.md`와 실제 노드 불일치

보고서를 표로 제시하고, **사용자 승인 후에만** 수정한다. `10-sources/`는 건드리지 않는다.
수정했다면 `log.md`에 `lint` 줄을 append.
