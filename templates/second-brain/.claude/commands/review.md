---
description: 주간 정비 — 인박스 비우기, 약한 노드 보강, 허브 갱신
---

`CLAUDE.md` §5 Weekly review 워크플로우를 따른다.

1. **인박스 처리**: `00-inbox/`의 각 메모를 검토 → 노드로 승격(`/ingest` 절차) 하거나 폐기 제안.
2. **episodic 캡처**: 이번 주의 결정·실험·사건을 사용자에게 물어 episodic 노드로 기록
   (`triggered_by`로 계기, 영향받은 노드에 `supports`/`refines` 연결).
3. **노드 보강**: `status: seedling` 노드를 점검, §4-A 3질문 기준으로 승격 후보 선정 —
   본격 증류는 `/distill`로 위임.
4. **그래프 정비**: 논증형 엣지 0개 노드에 엣지 보강(필요시 `/connect`), `topic` 허브 갱신.
5. **카탈로그 동기화**: `index.md`를 실제 노드와 맞춘다.
6. `log.md`에 `review` 줄 append.

먼저 이번 주에 할 일 목록을 제시하고 사용자와 우선순위를 정한 뒤 진행한다.
변경은 위키 계층에서만(`10-sources/` 불변).
