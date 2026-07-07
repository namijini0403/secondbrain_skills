---
name: extract-documents
description: Use when ingesting HWP, HWPX, PDF, XLSX, or DOCX files into a wiki/RAG — when a source in 10-sources/ is not plain text, when Read returns garbage on a binary file, or when a full-text dump of a Korean office document is needed.
---

# extract-documents — HWP/HWPX/PDF/XLSX/DOCX 텍스트 추출

## 개요

한국 학교·행정 문서(HWP/HWPX 포함)를 마크다운 텍스트로 추출한다.
원본은 절대 수정하지 않고, 옆에 `<이름>.<확장자>.extracted.md` 생성물을 만든다.
**원본이 진실의 원천, 추출본은 생성물**이다.

## 언제 쓰나

- second brain / curriculum-kb의 `/ingest` 대상이 HWP·HWPX·XLSX·DOCX일 때 (필수 — Read로 못 읽음)
- PDF가 크거나(20쪽↑) 전문(fulltext)이 통째로 필요할 때
  (몇 쪽만 필요하면 Claude Code의 Read 도구가 PDF를 직접 읽을 수 있음 — 그게 더 빠름)
- RAG 인덱싱용 코퍼스를 만들 때

## 사용법

```bash
python scripts/extract.py <파일> [<파일2> ...]        # 옆에 *.extracted.md 생성
python scripts/extract.py <파일> -o 출력.md           # 출력 경로 지정
python scripts/extract.py <파일> --stdout             # 표준출력으로
```

의존성: HWPX/XLSX/DOCX는 **표준 라이브러리만** 사용(설치 불필요).
- HWP(v5): `pip install olefile`
- PDF: `pip install pypdf`
- (권장) `pip install defusedxml` — 신뢰할 수 없는 문서의 XML 폭탄 방어

## 포맷별 동작

| 포맷 | 방식 | 비고 |
|------|------|------|
| `.hwpx` | zip 내 `Contents/section*.xml` 파싱 | 문단 단위 |
| `.hwp` | OLE `BodyText/Section*` 레코드(PARA_TEXT) 디코드 | HWP 5.x만. 암호·배포용(DRM)은 명확한 오류로 안내 |
| `.pdf` | pypdf 텍스트 레이어 | 쪽 번호 주석(`<!-- p.N -->`) 포함. 스캔 PDF는 OCR 필요 경고 |
| `.xlsx` | zip 내 XML 직접 파싱 | 시트별 마크다운 표. 5,000행 초과 시 생략 표시 |
| `.docx` | `word/document.xml` 파싱 | 문단 단위 |

## ingest 연계 규약

1. 추출본은 원본과 같은 폴더(예: `10-sources/`)에 `*.extracted.md`로 저장.
2. 노드의 `source:`는 **원본 파일**을 가리킨다(추출본 아님 — 추출본은 재생성 가능).
3. 추출 실패(암호·DRM·스캔 PDF)는 지어내지 말고 사용자에게 원인과 해결책을 보고.

## 흔한 실수

- **HWP 3.x / 배포용 HWP**: 미지원. 한글에서 "다른 이름으로 저장"(HWP 5.x 또는 HWPX) 후 재시도.
- **스캔 PDF**(텍스트 레이어 없음): 추출본에 경고가 붙는다. OCR 도구가 별도로 필요.
- **엑셀 수식**: 계산된 값(`<v>`)을 추출한다. 수식 문자열 자체는 안 나옴.
- **추출본을 원천으로 착각**: 추출본은 지워도 되는 생성물. 원본을 지우면 안 된다.
