---
name: school-app-security
description: Use when hardening or auditing a school/education app that handles student data — before a pilot deployment, before sharing an app with classes, when writing consent/privacy documents, or when a security review of auth/permissions/data collection is requested.
---

# school-app-security — 학교앱 보안·개인정보 패치 세트

## 개요

학생(특히 초등·아동) 데이터를 다루는 학교앱의 보안·개인정보 설계를 체계화한다.
실제 학교 배포 앱(학급 43개 반 규모 파일럿)에서 검증된 방법론의 일반화판.

**핵심 원칙: 문서보다 사실이 먼저다.** 보안 문서를 바로 쓰지 말고,
① 코드 전수조사 → ② 공통 사실 브리프(`_BRIEF.md`) → ③ 문서 세트 생성 → ④ 감사 순서로 간다.
문서들이 서로 다른 "사실"을 말하는 순간 전체 신뢰가 무너진다.

## 기준선

- OWASP **ASVS L2**, API Security Top 10, (모바일이면 MASVS)
- **개인정보보호법**, 개인정보의 안전성 확보조치 기준, 아동·청소년 개인정보보호 가이드라인
- **14세 미만은 법정대리인 동의** 필요 — 수집 최소화가 최우선 방어
- 우선순위 태그: **P0**=미충족 시 배포 금지 / **P1**=파일럿 전 / **P2**=정식 출시 전 / **P3**=장기 운영
- 초등학생 데이터 = 최고위험. 애매하면 더 보수적으로.

## 워크플로우

### 1단계 — 코드 전수조사 → `docs/security/_BRIEF.md`

앱 코드를 실제로 읽고(추측 금지) 다음을 한 문서로 정리한다. 이것이 모든 보안 문서의 공통 근거다:
- 아키텍처(클라이언트/서버/DB/배포처), 외부 통신 지점, 런타임 AI 호출 유무
- 인증·인가 방식(토큰 종류·수명·저장 위치, 비밀번호/PIN 해시, 역할 구분)
- **수집 데이터 전수 목록**(테이블/필드 단위) + **미수집 목록**(실명·연락처·위치 등)
- 현재 적용된 통제(파라미터 바인딩, 보안 헤더, 레이트리밋 등)와 **알려진 잔여 갭**(P1~P3)
- 불확실한 항목은 "확인 필요"로 표기(그럴듯한 거짓 금지). 코드가 바뀌면 브리프부터 갱신.

### 2단계 — 문서 세트 생성 (필요한 것만, `docs/security/`)

| 문서 | 내용 | 시점 |
|------|------|------|
| `DATA_CLASSIFICATION.md` | 데이터 분류·민감도 등급 | P0 |
| `THREAT_MODEL_STRIDE.md` | STRIDE 위협 모델링 | P1 |
| `RBAC_MATRIX.md` | 역할×권한 매트릭스 (학생/교사/관리자) | P0 |
| `CONSENT_FORM.md` | 법정대리인 동의서 (14세 미만) | P0 |
| `PRIVACY_POLICY.md` | 개인정보 처리방침 | P1 |
| `DATA_RETENTION_AND_DELETION_POLICY.md` | 보유·파기 정책 | P1 |
| `SCHOOL_INTERNAL_SECURITY_CHECKLIST.md` | 교내 운영 체크리스트(계정 배부·분실 대응) | P1 |
| `API_SECURITY_CHECKLIST.md` | 엔드포인트별 인증·인가·검증 점검표 | P1 |
| `INCIDENT_RESPONSE_RUNBOOK.md` | 사고 대응 절차(격리→통지→복구) | P2 |
| `DATA_FLOW_DIAGRAM.md` | 데이터 흐름도(수집→저장→위탁) | P2 |

모든 문서는 `_BRIEF.md`의 사실만 인용한다. 문서 간 사실 충돌 = 버그.

### 3단계 — 감사 (security-auditor 에이전트)

`agents/security-auditor.md`를 프로젝트 `.claude/agents/`에 설치하고 위임한다.
발견은 심각도(Critical/Important/Minor) + 근거(file:line) + 구체 수정안으로 보고받고,
수정은 코드 오너(메인 세션 또는 담당 에이전트)가 한다 — 감사자와 수정자의 분리.

### 4단계 — 반복 검증

수정 후 재감사(POST-FIX-VERIFICATION) → 잔여 갭을 P1~P3로 문서화 → 코드 변경 시 1단계부터.

## 검증된 설계 패턴 (아동 대상 앱)

- **수집 최소화가 곧 컴플라이언스**: 실명·생년월일·연락처를 아예 안 받으면 방어할 것도 줄어든다.
  로그인 = 반 코드 + 별명(실명 금지 안내) + PIN 같은 최소 신원 설계.
- **가명화 분리 저장**: 분석용 이벤트는 별도 DB에 가명 ID(HMAC(서버비밀, 학생ID))로만.
  재식별에 3요소(운영DB+분석DB+서버비밀)가 필요하도록 구조화.
- **동의 전 수집 방지 스위치**: 분석 DB 미설정 = no-op(수집 안 함)을 기본값으로 —
  법적 안전장치를 코드 레벨에 심는다. 우회 금지.
- **자유텍스트 격리**: 이벤트·로그에 자유텍스트/닉네임 진입을 화이트리스트로 구조적으로 차단.
- **fail-closed 부팅**: 운영 환경에서 필수 시크릿(JWT_SECRET 등) 미설정이면 서버가 아예 안 뜨게.
- **시크릿은 환경변수로만**: 코드·문서·메모에 값 비노출. 문서에는 이름만 적는다.

## 흔한 실수

- 브리프 없이 문서부터 쓰기 → 문서마다 사실이 달라짐.
- 감사 에이전트가 직접 코드를 고치게 하기 → 감사·수정 분리 원칙 위반.
- "나중에 지우면 되지"로 수집 범위를 넓히기 → 아동 데이터는 수집 순간부터 책임.
- 체크리스트만 채우고 코드 확인 안 하기 → 체크리스트는 코드 대조가 전제.
