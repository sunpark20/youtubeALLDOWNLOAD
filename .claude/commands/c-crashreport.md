Gmail에서 CrashReport 이메일을 읽고 분석 보고해줘.

사용자 추가 메시지: $ARGUMENTS

---

## 상태 파일

마지막으로 읽은 날짜를 아래 파일에 저장하여, 다음 실행 시 그 이후 리포트만 읽는다.

- **경로**: `/Users/sunguk/.claude/projects/-Users-sunguk-0-code-YT-Chita/memory/crashreport_last_read.md`
- **형식**: ISO 8601 날짜 한 줄 (예: `2026-03-14T04:15:14.000Z`)

## 수행할 작업

### 1. 상태 파일 확인

Read 도구로 상태 파일을 읽는다.
- 파일이 있으면 → 저장된 날짜를 `dateFrom`으로 사용
- 파일이 없거나 비어있으면 → 첫 실행. `dateFrom` 없이 전체 조회

### 2. 이메일 조회

`mcp__email-reader__get-messages` 도구를 호출한다:
```
subject: "crashreport"
includeFullContent: true
limit: 50
dateFrom: (상태 파일의 날짜, 첫 실행이면 생략)
```

### 3. 이메일 본문 디코딩

이메일 본문은 quoted-printable 인코딩되어 있을 수 있다.
- `=3D` → `=`, `=\n` → (줄 이음), `=E2=9C=85` → `✅` 등
- Bash에서 Python `quopri` 모듈로 디코딩하거나, 직접 패턴 치환

### 4. 리포트 분석 및 그룹핑

각 크래시 리포트에서 아래 정보를 추출하여 그룹핑:

| 추출 항목 | 찾는 방법 |
|-----------|-----------|
| **에러 유형** | 본문 첫 2~3줄의 Exception/Error 메시지 |
| **버전** | 이메일 제목 `[CrashReport] X.Y.Z - ErrorType` 에서 추출 |
| **사용자** | 본문의 Windows 경로 `C:\Users\{username}\...` 에서 추출 |
| **플랫폼** | 로그의 `Platform:` 라인에서 추출 |

### 5. 보고서 출력

한국어로 아래 형식의 요약 보고서를 출력한다:

```
## CrashReport 분석 보고서

### 기본 현황
- 총 리포트: N건
- 기간: YYYY-MM-DD ~ YYYY-MM-DD
- 버전: ...
- 플랫폼: ...
- 사용자: N명

### 에러 유형별 분류
| 에러 | 건수 | 영향 버전 | 영향 사용자 |
|------|------|-----------|-------------|
| ... | ... | ... | ... |

### 사용자별 현황
| 사용자 | 리포트 수 | 주요 에러 | 버전 |
|--------|-----------|-----------|------|
| ... | ... | ... | ... |

### 추가 발견사항
- WARNING 레벨 로그에서 발견된 부수적 문제들
- (ffmpeg 누락, mutex 충돌 등)
```

새 리포트가 0건이면: "새로운 크래시 리포트가 없습니다." 로 간단히 보고.

### 6. 상태 파일 갱신

조회한 리포트 중 가장 최신 날짜를 상태 파일에 저장한다.
- Write 도구로 `/Users/sunguk/.claude/projects/-Users-sunguk-0-code-YT-Chita/memory/crashreport_last_read.md` 에 날짜 한 줄만 기록
- 리포트가 0건이면 상태 파일을 갱신하지 않는다

## 주의사항

- 결과가 너무 클 경우 파일로 저장된다 → Bash에서 Python/jq로 파싱할 것
- 대량 리포트는 Python 스크립트로 일괄 분석하는 것이 효율적
- 코드 수정은 하지 않는다. 분석 및 보고만 수행
