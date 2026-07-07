---
description: 위키 건강 검진 — 모순/고아/오래된 노드/깨진 링크 점검
---

`CLAUDE.md` §5 Lint 워크플로우를 따른다. 범위: $ARGUMENTS (없으면 위키 전체)

`20-nodes/`, `30-topics/`, `index.md`, `log.md`를 훑어 다음을 점검하고 **보고서**를 먼저 낸다:
- 모순: 충돌하는 주장인데 `contradicts`로 안 묶인 노드 쌍
- 오래된 주장: `updated`가 오래됐고 최신 소스와 어긋나는 노드
- 고아 노드: `## Edges`가 비었거나 엣지 0개
- 누락 엣지: 명백히 연결돼야 하는데 빠진 관계
- 중복 노드 / 깨진 `[[링크]]` / `summary` 누락 / 템플릿·frontmatter 위반
- `index.md`와 실제 노드 불일치

보고서를 표로 제시하고, **사용자 승인 후에만** 수정한다. `10-sources/`는 건드리지 않는다.
수정했다면 `log.md`에 `lint` 줄을 append.
