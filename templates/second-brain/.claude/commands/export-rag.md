---
description: 위키를 외부 RAG 도구용 코퍼스(jsonl/md/graph)로 내보낸다
---

`.claude/skills/rag-export/SKILL.md`(rag-export 스킬)를 따른다. 대상 도구: $ARGUMENTS

1. `python .claude/skills/rag-export/scripts/export_corpus.py .` 실행 → `rag-export/` 생성.
2. 결과(노드/엣지 수, 미해결 엣지)를 보고한다. 미해결 엣지가 있으면 `/lint`를 권한다.
3. 사용자가 도구를 지정했으면(AnythingLLM/Open WebUI/Khoj/LightRAG/ChatGPT 등)
   스킬의 해당 연결 절차를 단계별로 안내한다. 지정 안 했으면 판단 가이드 표로 추천한다.
4. 주의 안내: 외부 도구는 읽기 전용 서피스(쓰기는 Claude Code만), `10-sources/` 원문은
   업로드 금지(저작권·개인정보), 위키 갱신 시 재내보내기 필요.
