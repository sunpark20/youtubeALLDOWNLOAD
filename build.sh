#!/bin/bash
# YT-Chita 빌드 및 코드 서명 스크립트
set -e

# =============================================================
# 설정
# =============================================================
APP_NAME="YT-Chita"
BUNDLE_ID="com.sunpark.YouTubeDownloader"
SIGN_IDENTITY="Developer ID Application: sunguk park (GA2LMK5XL2)"
ENTITLEMENTS="entitlements.plist"
DIST_DIR="dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"

echo "============================================"
echo " ${APP_NAME} 빌드 시작"
echo "============================================"

# =============================================================
# 1. 기존 빌드 정리
# =============================================================
echo ""
echo "[1/4] 기존 빌드 정리..."
rm -rf build dist

# =============================================================
# 2. PyInstaller 빌드
# =============================================================
echo ""
echo "[2/4] PyInstaller 빌드 중..."
source venv/bin/activate
pyinstaller YT-Chita.spec --clean --noconfirm
echo "✅ 빌드 완료"

# =============================================================
# 3. 코드 서명
# =============================================================
echo ""
echo "[3/4] 코드 서명 중..."

# 3-1. 내부 dylib/so 파일 먼저 서명 (deep signing)
echo "  → 내부 바이너리 서명 중..."
find "${APP_PATH}" -type f \( -name "*.dylib" -o -name "*.so" -o -name "*.framework" \) | while read -r file; do
    codesign --force --sign "${SIGN_IDENTITY}" \
        --entitlements "${ENTITLEMENTS}" \
        --options runtime \
        --timestamp \
        "${file}" 2>/dev/null || true
done

# 3-2. 메인 실행파일 서명
echo "  → 메인 실행파일 서명 중..."
codesign --force --sign "${SIGN_IDENTITY}" \
    --entitlements "${ENTITLEMENTS}" \
    --options runtime \
    --timestamp \
    "${APP_PATH}/Contents/MacOS/${APP_NAME}"

# 3-3. 앱 번들 전체 서명
echo "  → 앱 번들 서명 중..."
codesign --force --deep --sign "${SIGN_IDENTITY}" \
    --entitlements "${ENTITLEMENTS}" \
    --options runtime \
    --timestamp \
    "${APP_PATH}"

echo "✅ 코드 서명 완료"

# =============================================================
# 4. 서명 검증
# =============================================================
echo ""
echo "[4/4] 서명 검증 중..."
echo ""
echo "--- codesign verify ---"
codesign -dv --verbose=2 "${APP_PATH}" 2>&1
echo ""
echo "--- codesign assessment ---"
codesign --verify --deep --strict "${APP_PATH}" 2>&1 && echo "✅ 서명 검증 통과" || echo "⚠️ 서명 검증 경고 (개발용이면 정상)"

echo ""
echo "============================================"
echo " 빌드 완료!"
echo " 앱 위치: ${APP_PATH}"
echo "============================================"
echo ""
echo "실행: open ${APP_PATH}"
