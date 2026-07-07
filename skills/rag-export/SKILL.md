---
name: rag-export
description: Use when connecting the wiki to an external RAG or AI tool — when the user wants to chat with their vault outside Claude Code (AnythingLLM, Open WebUI, Khoj, LightRAG, RAGFlow, ChatGPT upload), asks "RAG로 만들어줘" / "다른 앱에서도 쓰고 싶어", or needs a corpus/graph export of the nodes.
---

# rag-export — 위키를 검증된 오픈소스 RAG 스택에 연결

## 개요

이 위키(20-nodes/30-topics)를 외부 RAG 도구가 소비할 수 있는 3가지 범용 포맷으로 내보내고,
2026년 기준 **검증된**(대규모 스타·활발한 유지보수) 오픈소스 도구별 연결 절차를 안내한다.

**원칙**: 위키가 단일 출처(source of truth), 내보내기는 생성물. 외부 도구는 **읽기 전용
질의 서피스**다(AGENTS.md 규약과 동일 — 쓰기는 Claude Code 한 곳).

## 내보내기

```bash
python scripts/export_corpus.py <위키루트>     # → <위키루트>/rag-export/ 생성
```

| 출력 | 포맷 | 먹는 도구 |
|------|------|-----------|
| `corpus.jsonl` | 노드당 1줄, 메타(id/type/summary/tags/edges) 동봉 | LlamaIndex·LangChain·LightRAG·커스텀 |
| `corpus.md` | 노드 경계를 보존한 단일 병합 마크다운 | AnythingLLM·Open WebUI·ChatGPT 업로드 |
| `graph.json` | 노드 + 타입 엣지(nodes[]/edges[]) | GraphRAG류·Neo4j·시각화 |

위키 갱신 후 재실행하면 전체 재생성(증분 아님). 원본은 절대 수정하지 않는다.

## 검증된 도구 카탈로그 (2026 기준 — 무엇을 고를까)

| 도구 | 무엇 | 이럴 때 | 난이도 |
|------|------|---------|--------|
| **AnythingLLM** | 데스크톱 앱, 제로설정 RAG(LanceDB 내장), 워크스페이스 | 개인이 설치 하나로 "내 문서와 대화" | ★ 최저 |
| **Open WebUI** | ChatGPT풍 셀프호스트 UI, Ollama 네이티브, 다중 사용자·RBAC | 교무실/팀 공용 챗 서버, 완전 로컬 LLM | ★★ |
| **Khoj** | 셀프호스트 "AI second brain", Obsidian/폰/WhatsApp 접속 | 위키를 Obsidian 볼트로 쓰면서 모바일 질의 | ★★ |
| **LightRAG** (HKU, EMNLP 2025) | 지식그래프+벡터 이중 검색, 경량(노트북 CPU 가능) | 이 위키처럼 **엣지가 자산**일 때 그래프 검색 | ★★★ |
| **RAGFlow** | 문서 파싱 특화 엔터프라이즈 RAG 엔진 | 복잡한 원문(계약서·보고서) 대량 처리 | ★★★ |
| **Microsoft GraphRAG** | 커뮤니티 계층 요약 기반 그래프 RAG | 연구·실험용(무겁고 LLM 비용 큼) | ★★★★ |
| LlamaIndex / LangChain / Haystack | 개발자용 프레임워크 | 직접 파이프라인을 코딩할 때 | 개발자 |

로컬 LLM이 필요하면 **Ollama**(Open WebUI·AnythingLLM·Khoj 모두 지원)가 표준.
학교 PC(GPU 없음)면 소형 모델 또는 클라우드 API 키 연결이 현실적.

## 도구별 연결 절차

### AnythingLLM (교사 추천 1순위 — 설치형)
1. https://anythingllm.com 데스크톱 앱 설치 → 워크스페이스 생성.
2. `rag-export/corpus.md` 업로드(또는 `20-nodes/` 폴더째 드래그 — md 그대로 먹음).
3. LLM 공급자 선택(Ollama 로컬 또는 API 키). 끝.
- 위키 갱신 시: corpus.md 재업로드.

### Open WebUI (+Ollama, 팀 공용)
1. Docker: `docker run -d -p 3000:8080 -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main`
2. Workspace → Knowledge → 컬렉션 생성 → `rag-export/corpus.md`(또는 노드 md들) 업로드.
3. 채팅에서 `#컬렉션명`으로 참조. 교사 계정별 권한 분리 가능.

### Khoj (Obsidian과 병행)
1. 셀프호스트(`pip install khoj` 또는 Docker) 후 콘텐츠 소스로 위키 폴더 지정.
2. Obsidian 플러그인 설치 시 볼트 안에서 바로 질의. 폰/웹에서도 같은 브레인 접근.

### LightRAG (그래프 검색 — 이 위키와 궁합 최고)
1. `pip install lightrag-hku` → 문서 삽입은 `corpus.jsonl`의 `text`를 순회 삽입.
2. 노드 요약·엣지를 이미 갖고 있으므로 `graph.json`을 사용자 정의 KG로 주입하는
   커스텀 파이프라인도 가능(LightRAG의 insert_custom_kg).
3. 질의 모드 hybrid 권장(그래프+벡터).

### ChatGPT (코드 없이)
Projects(또는 Custom GPT)에 `corpus.md` 업로드 + 각 템플릿의 `AGENTS.md` 내용을
instruction으로 붙여넣기(읽기 전용·인용 필수·없으면 "없음" 규약).

## 판단 가이드

- "설치 하나로 끝, 혼자 씀" → **AnythingLLM**
- "동학년/교무실이 같이 씀, 완전 로컬" → **Open WebUI + Ollama**
- "Obsidian으로 위키 보면서 폰에서도 질의" → **Khoj**
- "requires 체인·contradicts 같은 **엣지를 검색에 활용**" → **LightRAG**
- "원문 PDF 수백 개를 통째로" → **RAGFlow** (위키 없이 원문 직접 인덱싱)

## 흔한 실수

- 외부 도구에서 노드를 고치고 위키에 반영 안 함 → **쓰기는 Claude Code만**. 외부는 읽기 전용.
- `10-sources/` 원문(저작권 자료·개인정보)까지 통째로 업로드 → **20-nodes/30-topics만** 내보낸다.
  export 스크립트도 소스 폴더는 건드리지 않는다.
- 클라우드 도구에 학생 개인정보가 든 노드 업로드 → 업로드 전 내용 확인은 사용자 책임.
- 위키가 작을 때(노드 <30개) RAG 스택부터 깔기 → 그냥 Claude Code 질의가 낫다.
  RAG는 위키가 커져 컨텍스트에 안 들어갈 때 가치가 생긴다.
