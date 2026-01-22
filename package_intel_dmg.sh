#!/bin/bash
set -e

APP_NAME="YoutubeALL_downloader"
APP_SOURCE_DIR="dist_intel"
DMG_NAME="${APP_NAME}_Intel_Installer.dmg"
STAGING_DIR="dmg_staging_intel"

echo "🧹 기존 빌드 정리 중..."
rm -rf "$STAGING_DIR"
rm -f "$APP_SOURCE_DIR/$DMG_NAME"

echo "📂 DMG 구성 요소 준비 중..."
mkdir -p "$STAGING_DIR"
cp -R "$APP_SOURCE_DIR/$APP_NAME.app" "$STAGING_DIR/"

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
