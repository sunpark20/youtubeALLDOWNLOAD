아래 빌드 관련 지식을 숙지하고 사용자의 빌드 요청을 처리해줘.

사용자 추가 메시지: $ARGUMENTS

---

## 빌드 대상

| 플랫폼 | 러너 | 결과물 |
|--------|------|--------|
| Mac M-Chip (arm64) | `macos-latest` | `YB-Mac-M-Chip.dmg` |
| Mac Intel (x86_64) | `macos-15-intel` | `YB-Mac-Intel.dmg` |
| Windows 10/11 64bit | `windows-latest` | `YB-Windows10_11-64bit.zip` |

## 러너 주의사항

- **인텔 빌드 러너는 반드시 `macos-15-intel` 사용** (`macos-15-large`는 유료라 결제 오류 발생)
- arm64 러너에서 Rosetta 2로 x86_64 빌드: GitHub Actions에서 **불가**
- Universal2 빌드: PyInstaller에서 **비실용적**

## 인텔맥 entitlements 필수 (절대 삭제 금지)

`entitlements.plist`에 아래 2개가 반드시 있어야 인텔맥에서 앱이 실행됨:
- `com.apple.security.cs.allow-unsigned-executable-memory`
- `com.apple.security.cs.disable-library-validation`

없으면 PyInstaller가 추출한 .so/.dylib 로드가 OS에 의해 차단되어 앱 실행 자체가 안 됨 (Python 로드 전 kill).

## 빌드 절차

1. **버전 번호 확인**: 사용자에게 정확한 버전 번호를 반드시 확인받고 진행
2. **버전 올리기**: `src/utils/config.py`의 `APP_VERSION` 수정
3. **릴리즈 노트 작성**: `build.yml`의 `body:` 섹션 전체를 새 버전에 맞게 수정
4. **빌드 전 검증**: `python -c "import py_compile; ..."` 등으로 주요 파일 구문 오류 확인
5. **커밋 & 푸시**
6. **태그 생성 & 푸시** → 빌드 자동 트리거
7. `gh run watch`로 빌드 모니터링

## 태그 재생성 (빌드 재실행)

```bash
# 1. 태그 삭제 (로컬 + 리모트)
git tag -d v1.x.x
git push origin :refs/tags/v1.x.x

# 2. Release도 삭제 (있으면)
gh release delete v1.x.x --yes

# 3. 태그 재생성 + 푸시
git tag v1.x.x
git push origin v1.x.x
```

## 빌드 실패 시 대처

| 실패 유형 | 원인 | 대처 |
|-----------|------|------|
| 인텔맥 앱 실행 안 됨 | entitlements 누락 | `entitlements.plist` 확인 |
| Notarization 실패 | Apple 인증서/비밀번호 만료 | GitHub Secrets 확인 |
| FFmpeg 다운로드 실패 | 외부 URL 변경 | `build.yml`의 FFmpeg URL 확인 |
| PyInstaller 에러 | 의존성 변경 | `requirements.txt`, `.spec` 파일 확인 |

## 관련 파일

- `.github/workflows/build.yml` — 빌드 워크플로우 (태그 `v*` 푸시로 트리거)
- `YT-Chita.spec` — PyInstaller 설정
- `entitlements.plist` — macOS 코드 서명 권한
- `src/utils/config.py` — 앱 버전
