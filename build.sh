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
echo "[1/5] 기존 빌드 정리..."
rm -rf build dist

# =============================================================
# 2. PyInstaller 빌드
# =============================================================
echo ""
echo "[2/5] PyInstaller 빌드 중..."
source venv/bin/activate
pyinstaller YT-Chita.spec --clean --noconfirm
echo "✅ 빌드 완료"

# =============================================================
# 3. 코드 서명
# =============================================================
echo ""
echo "[3/5] 코드 서명 중..."

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
echo "[4/5] 서명 검증 중..."
echo ""
echo "--- codesign verify ---"
codesign -dv --verbose=2 "${APP_PATH}" 2>&1
echo ""
echo "--- codesign assessment ---"
codesign --verify --deep --strict "${APP_PATH}" 2>&1 && echo "✅ 서명 검증 통과" || echo "⚠️ 서명 검증 경고 (개발용이면 정상)"

# =============================================================
# 5. DMG 생성 (Drag to Applications)
# =============================================================
echo ""
echo "[5/5] DMG 생성 중..."

# DMG 배경 이미지가 없으면 생성
if [ ! -f "resource/dmg-background.png" ]; then
    echo "  → DMG 배경 이미지 생성 중..."
    python resource/create_dmg_bg.py
fi

DMG_PATH="${DIST_DIR}/YB-Mac-$(uname -m).dmg"

# create-dmg 설치 확인
if ! command -v create-dmg &>/dev/null; then
    echo "  → create-dmg 설치 중..."
    brew install create-dmg
fi

# 기존 DMG 제거
rm -f "${DMG_PATH}"

create-dmg \
    --volname "YT-Chita" \
    --volicon "resource/icon.icns" \
    --background "resource/dmg-background.png" \
    --window-pos 200 120 \
    --window-size 660 400 \
    --icon-size 80 \
    --icon "YT-Chita.app" 180 190 \
    --app-drop-link 480 190 \
    --hide-extension "YT-Chita.app" \
    --no-internet-enable \
    "${DMG_PATH}" \
    "${APP_PATH}"

echo "✅ DMG 생성 완료"

echo ""
echo "============================================"
echo " 빌드 완료!"
echo " 앱 위치: ${APP_PATH}"
echo " DMG 위치: ${DMG_PATH}"
echo "============================================"
echo ""
echo "실행: open ${APP_PATH}"
echo "DMG 확인: open ${DMG_PATH}"
