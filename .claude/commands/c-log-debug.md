오늘 날짜의 yt-dlp 로그 파일을 읽고 에러/경고를 분석해줘.

사용자 추가 메시지: $ARGUMENTS

---

## 로그 파일 위치

플랫폼별 경로 (코드: `src/utils/logger.py`의 `_get_log_dir()`):

| 플랫폼 | 경로 |
|--------|------|
| macOS | `~/Library/Logs/YT-Chita/app_YYYYMMDD.log` |
| Windows | `%APPDATA%/YT-Chita/Logs/app_YYYYMMDD.log` |
| Linux | `~/.local/share/YT-Chita/logs/app_YYYYMMDD.log` |

Windows 로그는 사용자가 프로젝트 루트에 직접 올리는 경우도 있음 → `app_YYYYMMDD.log` 패턴으로 Glob 검색할 것.

## 수행할 작업

1. 오늘 날짜의 로그 파일을 찾기 (Mac 경로 우선, 없으면 프로젝트 루트 Glob)
2. Grep으로 `ERROR`, `WARNING` 라인을 먼저 추출하고, 필요시 전후 문맥을 Read로 확인
3. 발견된 문제를 아래 관점에서 분석:
   - 에러 원인과 해결 방법
   - yt-dlp 버전 정보 (로그 초반의 `yt-dlp version:` 라인 확인)
   - 반복되는 패턴이 있는지 (같은 에러가 여러 번 발생)
   - 플랫폼별 차이 (Windows vs Mac 로그가 모두 있을 때)
4. 문제가 없으면 "이상 없음"으로 간단히 보고
5. 사용자가 추가 메시지를 남겼으면 그 맥락에 맞춰 분석

## 무시해도 되는 경고 패턴

| 경고 메시지 | 설명 |
|------------|------|
| `Preferring "ko" translated fields` | 한국어 메타데이터 우선 사용 — 정상 동작 |
| `[jsc] Remote components challenge solver ... were skipped` | yt-dlp 2026.03.13+ EJS 관련. deno 미설치 시 나타남. 다운로드에 영향 없음 (고화질 포맷 일부 누락 가능) |
| `n challenge solving failed` | 위와 동일 원인 |
