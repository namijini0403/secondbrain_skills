---
description: seedling 노드를 3질문(왜/긴장/적용)으로 증류해 growing으로 승격한다
---

`CLAUDE.md` §5 Distill 워크플로우 + §7-B 의도 계약을 따른다. 대상: $ARGUMENTS

1. **작업 브리프**(§7-B): 대상 노드 목록·위임 계획(node-distiller/Sonnet)·웹 검증 여부를
   먼저 제시한다. 인자가 없으면 `status: seedling` 노드를 인바운드 링크 수 순으로 정렬해
   상위 5~8개를 후보로 제안하고 확인받는다.
2. 노드당 1건으로 **node-writer가 아닌 node-distiller**(Sonnet)에 위임. 프롬프트에 반드시 동봉:
   대상 노드 경로, `source:` 원천 경로, 관련 기존 노드 경로 3~6개(오케스트레이터가 선별),
   해당 topic 허브 경로.
3. 결과 검수(오케스트레이터): §4-A 3질문 충족, 새 엣지 대상 실재, summary 한 문장,
   원천 무수정. 실패 시 §7-A 3-스트라이크(재시도→Opus 승격/인라인).
4. 배치가 노드 3개 이상이면 wiki-linter 스팟체크(§7-A 검증 게이트).
5. `log.md`에 `- YYYY-MM-DD | review | [[노드들]] | 출처: <근거> | 증류 요약` append.
6. **표준 보고**(§7-B): 승격 노드·새 엣지·검증 결과·의도 정합을 요약한다.
