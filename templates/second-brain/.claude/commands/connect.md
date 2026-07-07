---
description: 누락된 논증형 엣지(supports/contradicts/refines)를 발굴해 그래프를 촘촘하게 만든다
---

`CLAUDE.md` §5 Connect 워크플로우 + §3-A 밀도 가이드 + §7-B 의도 계약을 따른다.
범위: $ARGUMENTS (없으면 위키 전체)

1. **edge-weaver**(Sonnet, 읽기 전용)에 위임해 누락 엣지 후보 표를 받는다.
   contradicts > supports/refines > 기타 순으로 우선. topic/near 후보는 최소화.
2. 오케스트레이터가 후보를 검증한다 — **양쪽 노드 본문을 실제로 읽고** 관계가 성립하는지
   판단. 성립 안 하는 후보는 버린 이유와 함께 표에서 제외.
3. 검증된 후보를 사용자에게 표로 제시하고 **승인분만** 적용:
   - 방향 있는 엣지는 출발 노드의 `## Edges`에. contradicts는 양방향.
   - 엣지를 받은 노드의 `updated`는 변경하지 않는다(본문 무변경 시).
4. 논증형 엣지 0개 노드 목록은 /distill 후보로 넘긴다(여기서 억지 연결하지 않는다).
5. `log.md`에 `- YYYY-MM-DD | update | (connect N건) | 출처: - | 요약` append.
6. **표준 보고**(§7-B): 적용/기각 건수와 대표 발견(특히 새 contradicts)을 요약한다.
