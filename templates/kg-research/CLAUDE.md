# CLAUDE.md — 연구용 지식그래프 하네스 (research-grade)

이 폴더는 **논문용 측정 도구**를 만드는 하네스다. 교육과정(또는 다른 도메인)의 지식그래프를
"빨리 많이"가 아니라 **"느려도 방어 가능하게"** 구축한다. `templates/curriculum-kb`가 수업·앱용
프로토타입이라면, 이 하네스는 심사자의 공격 — **누가 무슨 근거로 판정했나 / LLM 순환성 /
입자성 자의성** — 을 방어해야 하는 연구 자산용이다.

> 이 그래프는 데이터가 아니라 **자(尺)다.** 자가 흔들리면 그걸로 잰 모든 결과가 무효다.

---

## 0. 세션 시작 체크리스트 (모든 에이전트, 매 세션)

1. 이 문서 전체를 읽는다.
2. 맡은 작업 유형에 해당하는 코드북(`codebook/`)과 `schema/SCHEMA.md`를 읽는다.
   **기억에 의존 금지 — 코드북은 개정된다. 반드시 현재 버전을 읽는다.**
3. `python scripts/validate.py` 를 실행해 현재 상태가 깨끗한지 확인한다.
   시작 전부터 ERROR가 있으면 **작업하지 말고 보고**한다 (남의 오류 위에 쌓지 않기).

## 1. 진실의 원천과 파일 맵

```
kg-research/
├── CLAUDE.md            ← 이 문서 (하네스)
├── codebook/            ← 판정 기준 (01 노드, 02 엣지, 03 코딩 프로토콜) — 직접 작성
├── schema/SCHEMA.md     ← 데이터 스키마 정의 — 직접 작성
├── data/
│   ├── nodes.csv        ★ 진실의 원천
│   ├── edges.csv        ★ 진실의 원천
│   ├── lexicon.csv        용어 정규화 사전
│   ├── exceptions.csv     승인된 규칙 예외
│   ├── decisions.md       판정·조정 로그 (append-only)
│   ├── annotations/       이중 코딩 원자료 (append-only)
│   └── delphi/            델파이 원자료 (전문가 패널을 쓸 경우)
├── scripts/validate.py    무결성 검사 (품질 게이트) — 스키마에 맞춰 작성
├── scripts/irr.py         코더 간 신뢰도 (Cohen's κ 등)
└── reports/               검사 보고서 (생성물)
```

- **진실의 원천은 `data/nodes.csv`·`data/edges.csv`뿐이다.** vault·시각화·Neo4j는 생성물.
- 원천 문서(교육과정 별책 등)는 별도 폴더 — **읽기 전용**.
- 프로토타입 위키(curriculum-kb 등)는 아이디어 참고용 재료다.
  **근거(evidence)로 인용 금지** — 그 안의 코드·문구·관계는 미검증(provisional)이다.

## 2. 불변 규칙 (INVARIANTS) — 위반은 곧 연구 무효

- **I1 (verbatim)**: 원문 코드·문구는 원본 그대로. 기억으로 재구성 금지.
  원문을 확인하지 못했으면 만들지 말고 `notes: 원문대조필요` + status `draft`.
- **I2 (provenance)**: 근거 없는 엣지 금지. 모든 엣지는 proposer / evidence_type /
  coder / agreement를 가진다. 최상위 증거 등급은 원문 인용 필수.
- **I3 (LLM은 후보만)**: LLM(이 문서를 읽는 에이전트 포함)은 엣지·노드를
  `status: candidate` / `draft`로만 만들 수 있다. **`coded` 이상으로의 승격은 인간 판정
  기록(annotations 또는 decisions.md)이 있을 때만** 하고, 승격 작업 자체도 인간 지시로만 한다.
- **I4 (정의문 동결)**: 확정(adjudicated) 이상 노드의 definition은 임베딩·측정 입력이다.
  수정하려면 decisions.md 기록 + "임베딩 재추출 필요" 명시. 조용한 수정 절대 금지.
- **I5 (append-only)**: decisions.md, annotations/, log는 과거 줄 수정·삭제 금지.
  CSV 행 삭제 금지 — 폐기는 status(`rejected`)로.
- **I6 (스키마·코드북 동결)**: 스키마와 코드북의 **개정은 인간 승인 전 금지.**
  에이전트는 개정안을 제안만 할 수 있다. "코드북이 이 사례를 못 다룬다"고 판단되면
  임의 해석하지 말고 판정 보류 + 보고.
- **I7 (품질 게이트)**: data/를 수정한 모든 작업은 `python scripts/validate.py`
  **통과(ERROR 0) 없이는 완료가 아니다.** WARN은 완료 보고에 목록으로 첨부.
- **I8 (모르면 비워두기)**: 값이 불확실하면 그럴듯하게 채우지 말고 비우거나 notes에 TODO.
  **빈칸 > 그럴듯한 거짓.** 이 연구에서 조용한 추측은 데이터 오염이다.
- **I9 (검증용 데이터 격리)**: 검증에 쓸 외부 신호(예: 교과서 순서)를 구축 근거로 쓰지 않는다
  (순환성 방지 — 검증용으로 예약).
- **I10 (안전한 쓰기)**: data/*.csv를 스크립트로 수정할 때는 ① 수정 전 `git add -A &&
  git commit`으로 스냅샷, ② 임시 파일에 쓴 뒤 원자적 교체(replace), ③ 수정 후
  validate 통과 확인. (부분 쓰기로 인한 데이터 유실 방지 규칙 — 위반 금지.)

## 3. 권한 매트릭스 — 누가 무엇을 하나

| 작업 | 인간(연구자) | 상위 모델 | 소형 모델 |
|------|:--:|:--:|:--:|
| 코드북·스키마 개정 승인 | ✅ | 제안만 | 제안만 |
| 엣지·노드 최종 판정 (coded 이상 승격) | ✅ | ❌ | ❌ |
| 조정 회의·델파이 | ✅ | ❌ | ❌ |
| 엣지 후보 제안 (candidate 생성) | ✅ | ✅ | ⚠️ 소량만 |
| 원문 → 노드 초안 분해 (draft 생성) | ✅ | ✅ | ✅ (검수 전제) |
| 원문 verbatim 전사 | ✅ | ✅ | ✅ |
| CSV 정형 작업 (필드 채우기·형식 정리) | ✅ | ✅ | ✅ |
| validate/irr 실행·보고 | ✅ | ✅ | ✅ |
| 판정 기록의 CSV 반영 (인간 판정 → status 갱신) | ✅ | ✅ | ✅ (기록 대조 필수) |
| 분석 스크립트 작성 | ✅ | ✅ | ⚠️ 명세 있을 때만 |

원칙: **판단은 위로, 노동은 아래로.** 코드북 해석이 필요한 작업일수록 위임 금지.

## 4. 표준 작업 프로토콜 (data/를 건드리는 모든 배치 공통)

```
① 읽기   : CLAUDE.md + 해당 코드북 + SCHEMA.md (현재 버전)
② 시작검사: python scripts/validate.py → ERROR 있으면 중단·보고
③ 작업   : 배치 단위(노드/엣지 ~30개)로. 코드북 조항 번호를 근거로 남기며 진행
④ 종료검사: python scripts/validate.py → ERROR 0 될 때까지 수정 (단, 남의 데이터를
            "검사 통과를 위해" 고치지 않는다 — 내 배치만. 기존 오류는 보고)
⑤ 보고   : 아래 완료 보고 형식으로. 애매했던 판정은 반드시 [보류] 목록에
```

**완료 보고 형식** (서브에이전트는 이것이 최종 출력):
```
STATUS: DONE | PARTIAL | FAILED
배치: <범위>
생성: 노드 N개 (draft), 엣지 후보 M개 (candidate)
validate: ERROR 0 / WARN k  (WARN 목록 첨부)
[보류] 코드북으로 판정 불가했던 사례: (없으면 "없음")
  - <사례> — 관련 조항 <번호>, 무엇이 애매한가
[제안] 코드북 개정 제안: (없으면 "없음")
```

## 5. 작업 유형별 Definition of Done

- **원문 ingest**: 원본에서 verbatim 전사(쪽 기록) → 노드 draft → 코드북 절차로 분해 →
  엣지 후보(candidate) → validate 통과 → 보고. **원문 페이지를 실제로 읽지 않았으면
  FAILED로 보고** (I1).
- **엣지 후보 생성**: 지정된 노드 집합에 대해 코드북 결정 트리로 후보 나열 →
  모두 `candidate`/proposer에 자기 모델 ID → 쌍마다 판정 테스트 결과를 보고서에 적어
  인간 판정 자료로 제공.
- **판정 반영**: annotations/decisions.md의 인간 판정 기록과 **1:1 대조**하며 status·
  agreement 갱신. 기록에 없는 항목을 승격했다면 그 자체가 FAILED.
- **스크립트 작업**: 기존 데이터로 실행 확인 + 고장 케이스 1개 이상 사본 테스트.

## 6. 서브에이전트 위임 규칙

- **모델 선택**: verbatim 전사·CSV 정형·판정 반영 = 소형 모델 충분.
  개념 분해·엣지 후보 = 상위 모델 (판단 품질이 다름).
  코드북·스키마·분석 설계 = 위임하지 말 것 (인간 + 최상위 모델 인라인).
- **배치 크기**: 한 번에 5~8단위. 크게 주면 후반부 품질이 떨어진다.
- **연속 분해는 인라인 우선**: 노드 간 일관성이 중요한 연쇄 작업은 위임보다 인라인이
  안전하다. 위임한다면 같은 영역은 같은 에이전트에 몰아준다.
- **3-스트라이크**: STATUS: FAILED 또는 validate ERROR가 남으면 실패 이유를 덧붙여
  같은 모델에 최대 3회 재시도 → 그래도 실패면 상위 모델 승격 또는 인라인 수행.
  **절대 금지: 검사를 통과시키려고 규칙 쪽을 완화하는 것.**
- **위임 프롬프트에는 아래 프리앰블을 그대로 포함**한다:

```text
[연구용 지식그래프 작업 프리앰블 — 수정 없이 포함할 것]
너는 논문용 측정 도구(지식그래프)를 만드는 보조 코더다. 시작 전에
CLAUDE.md, schema/SCHEMA.md, 그리고 지시받은 코드북을 전부 읽어라.
절대 규칙: (1) 원문 코드·문구는 원문을 직접 읽고 verbatim으로만 — 기억으로 짓지 마라.
(2) 너의 산출물은 전부 status=draft/candidate다 — coded 이상 승격 금지. (3) 확실하지 않은
값은 그럴듯하게 채우지 말고 비우고 notes에 TODO를 적어라 — 이 연구에서 조용한 추측은
데이터 오염이다. (4) 판정이 애매하면 코드북을 임의 해석하지 말고 [보류]로 보고해라.
(5) 작업 후 python scripts/validate.py 를 실행해 ERROR 0을 확인하고, CLAUDE.md §4의
완료 보고 형식으로만 최종 보고해라. 규칙과 작업량이 충돌하면 규칙이 이긴다.
```

## 7. 로그 규약

- 배치 완료 시 **`log.md`** (이 폴더 루트)에 1줄 append:
  `- YYYY-MM-DD | <action> | <배치> | <모델/코더> | ERROR 0/WARN k | 메모`
  (action ∈ ingest / candidate / apply-judgment / lint / script)
- decisions.md는 **판정·조정·개정** 전용.

## 8. 시작하기 (이 템플릿을 쓰는 법)

1. `schema/SCHEMA.md`에 nodes.csv/edges.csv의 열 정의를 먼저 확정한다
   (권장 열 — nodes: id,type,label,definition,grade_band,source_doc,source_page,status,notes /
   edges: id,src,dst,edge_type,evidence_type,evidence,proposer,coder,agreement,status,notes).
2. `codebook/01-nodes.md`(노드 판정 기준), `02-edges.md`(엣지 결정 트리),
   `03-protocol.md`(코딩 절차·이중 코딩·조정 규칙)를 작성한다 — 여기가 연구의 심장.
3. `scripts/validate.py`를 스키마에 맞춰 작성한다(필수 열·타입·참조 무결성·status 규칙 검사).
4. 파일럿 배치(성취기준 5~8개)로 코드북을 시험하고 v0.1을 확정한 뒤 본 코딩에 들어간다.
