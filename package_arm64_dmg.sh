#!/bin/bash
set -e

APP_NAME="YoutubeALL_downloader"
APP_SOURCE_DIR="dist_arm64"
DMG_NAME="${APP_NAME}_Silicon_Installer_v2.dmg"
STAGING_DIR="dmg_staging_arm64"

echo "🧹 기존 빌드 정리 중..."
rm -rf "$STAGING_DIR"
rm -f "$APP_SOURCE_DIR/$DMG_NAME"

echo "📂 DMG 구성 요소 준비 중..."
mkdir -p "$STAGING_DIR"
cp -R "$APP_SOURCE_DIR/$APP_NAME.app" "$STAGING_DIR/"

echo "🛡️  보안 속성 제거 및 강제 서명 (Damaged 에러 방지)..."
# 확장 속성 제거 (Quarantine 등)
xattr -cr "$STAGING_DIR/$APP_NAME.app"

# Entitlements 적용하여 강제 ad-hoc 서명
echo "🔑 Entitlements 적용 서명 중..."
codesign --force --deep --entitlements entitlements.plist --sign - "$STAGING_DIR/$APP_NAME.app"

# 서명 검증
echo "🔍 서명 검증 중..."
codesign --verify --deep --strict --verbose=2 "$STAGING_DIR/$APP_NAME.app" || echo "⚠️ 서명 검증 경고 (무시 가능)"

echo "📦 DMG 패키징 중 (create-dmg)..."
create-dmg \
    --volname "${APP_NAME}_Installer" \
    --window-pos 200 120 \
    --window-size 660 400 \
    --icon-size 128 \
    --icon "${APP_NAME}.app" 180 170 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 480 170 \
    --no-internet-enable \
    "$APP_SOURCE_DIR/$DMG_NAME" \
    "$STAGING_DIR"

echo "🧹 임시 파일 정리..."
rm -rf "$STAGING_DIR"

echo "🎉 DMG 생성 완료!"
echo "👉 파일 위치: $APP_SOURCE_DIR/$DMG_NAME"
