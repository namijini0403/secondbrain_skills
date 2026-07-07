---
description: 교육과정 위키를 외부 RAG 도구용 코퍼스(jsonl/md/graph)로 내보낸다
---

`.claude/skills/rag-export/SKILL.md`(rag-export 스킬)를 따른다. 대상 도구: $ARGUMENTS

1. `python .claude/skills/rag-export/scripts/export_corpus.py .` 실행 → `rag-export/` 생성.
   (graph.json에는 requires 결손 체인·aligns_to 정렬이 타입 엣지로 보존된다 —
   그래프 검색 도구(LightRAG 등)와 궁합이 좋다.)
2. 결과(노드/엣지 수, 미해결 엣지)를 보고하고, 미해결 엣지가 있으면 `/lint`를 권한다.
3. 사용자가 도구를 지정했으면 스킬의 해당 연결 절차를 안내한다.
4. 주의: 외부 도구는 읽기 전용, `10-sources/` 원문 별책은 업로드 금지(저작권),
   위키 갱신 시 재내보내기.
