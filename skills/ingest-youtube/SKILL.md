---
name: ingest-youtube
description: Use when a source to ingest is a YouTube video or link — lecture, training (연수), seminar recording, or when the user asks to summarize/ingest a video into the wiki or RAG corpus. Produces a timestamped markdown transcript with deep links.
---

# ingest-youtube — 유튜브 영상을 타임스탬프 전사본으로

## 개요

유튜브 영상(강의·연수·세미나)을 **타임스탬프 딥링크가 달린 마크다운 전사본**으로 변환한다.
전략은 검증된 파이프라인의 이식: **자막 우선, 없으면 Whisper 폴백.**

1. **yt-dlp로 자막(.vtt)만 다운로드** — 정식 자막과 자동 생성 자막 둘 다 시도.
   영상은 안 받는다. **YouTube API 키 불필요.**
2. **VTT 직접 파싱** — 인라인 태그·HTML 엔티티 정리, 자동자막 특유의 롤링 중복
   (직전 자막 꼬리가 다음 자막 머리에 반복) 을 suffix/prefix 매칭으로 제거.
   시작 시각을 보존해 `youtu.be/<id>?t=초` 딥링크 생성 → 노드에서 원본 구간 인용 가능.
3. **자막이 없으면 (선택) Whisper STT** — 오디오만 추출해 OpenAI Whisper API로 전사
   (타임스탬프 유지). **과금 발생** — OPENAI_API_KEY 있을 때만, 실행 전 사용자에게 알린다.

## 사용법

```bash
python scripts/ingest_youtube.py "https://youtu.be/<id>"            # → youtube-<id>.extracted.md
python scripts/ingest_youtube.py "<url>" -o 10-sources/제목.extracted.md
```

환경변수: `TRANSCRIPT_METHOD`(기본 captions-then-whisper | captions-only),
`TRANSCRIPT_LANG`(기본 ko), `STT_MODEL`(기본 whisper-1).

의존성: `pip install yt-dlp`. Whisper 폴백 시에만 `pip install openai` + `OPENAI_API_KEY`.

## ingest 연계 규약

1. 전사본은 `10-sources/`에 저장 — 원본은 유튜브 영상이므로 노드 `source:`에는
   **영상 URL이 담긴 전사본**을 가리킨다.
2. 노드 본문에서 특정 주장 인용 시 전사본의 딥링크(`?t=초`)를 그대로 옮겨 근거로 남긴다.
3. 자동 자막은 오인식(고유명사·숫자)이 있다 — **핵심 수치·용어는 영상에서 직접 확인**하고,
   미확인이면 "확인 필요" 표기(그럴듯한 거짓 금지).
4. 채널/재생목록 전체는 URL을 순회하며 반복 실행(대량이면 사용자에게 개수 확인).

## 흔한 실수

- 자동 자막 텍스트를 검증 없이 verbatim 인용 ("202 개정" 같은 오인식이 흔함).
- Whisper 폴백을 사용자 고지 없이 실행 (비용 원칙 위반 — 반드시 먼저 알린다).
- 전사본을 위키 노드처럼 취급 — 이건 원천(source)이다. 노드는 /ingest로 따로 만든다.
- 25MB 초과 오디오(약 25분↑ 고음질)를 Whisper에 통째로 — 한도 초과. 분할 필요.
