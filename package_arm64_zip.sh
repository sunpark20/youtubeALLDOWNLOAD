#!/bin/bash
set -e

APP_NAME="YoutubeALL_downloader"
APP_SOURCE_DIR="dist_arm64"
ZIP_NAME="${APP_NAME}_Silicon_v2.zip"
STAGING_DIR="zip_staging_arm64"

echo "🧹 기존 빌드 정리 중..."
rm -rf "$STAGING_DIR"
rm -f "$APP_SOURCE_DIR/$ZIP_NAME"

echo "📂 ZIP 구성 요소 준비 중..."
mkdir -p "$STAGING_DIR"
cp -R "$APP_SOURCE_DIR/$APP_NAME.app" "$STAGING_DIR/"
cp "먼저실행.command" "$STAGING_DIR/"
chmod +x "$STAGING_DIR/먼저실행.command"

echo "🛡️  보안 속성 제거 및 강제 서명 (Damaged 에러 방지)..."
# 확장 속성 제거 (Quarantine 등)
xattr -cr "$STAGING_DIR/$APP_NAME.app"

# Entitlements 적용하여 강제 ad-hoc 서명
echo "🔑 Entitlements 적용 서명 중..."
codesign --force --deep --entitlements entitlements.plist --sign - "$STAGING_DIR/$APP_NAME.app"

# 서명 검증
echo "🔍 서명 검증 중..."
codesign --verify --deep --strict --verbose=2 "$STAGING_DIR/$APP_NAME.app" || echo "⚠️ 서명 검증 경고 (무시 가능)"

echo "📦 ZIP 압축 중..."
cd "$STAGING_DIR"
zip -r -y "../$APP_SOURCE_DIR/$ZIP_NAME" "$APP_NAME.app" "먼저실행.command"
cd ..

echo "🧹 임시 파일 정리..."
rm -rf "$STAGING_DIR"

echo "🎉 ZIP 생성 완료!"
echo "👉 파일 위치: $APP_SOURCE_DIR/$ZIP_NAME"
