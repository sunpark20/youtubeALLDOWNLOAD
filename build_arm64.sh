#!/bin/bash
set -e

log() {
    echo -e "\n[ARM64-Build] $1"
}

ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    log "❌ 이 스크립트는 Apple Silicon (ARM64) Mac 전용입니다."
    log "현재 아키텍처: $ARCH"
    exit 1
fi

log "✅ Apple Silicon (ARM64) 확인"

cd "$(dirname "$0")"

VENV_NAME="venv_arm64"

if [ ! -d "$VENV_NAME" ]; then
    log "🔨 ARM64용 가상환경($VENV_NAME) 생성 중..."
    /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv "$VENV_NAME"
else
    log "♻️  기존 가상환경($VENV_NAME) 사용"
fi

source "$VENV_NAME/bin/activate"

PY_ARCH=$(python3 -c "import platform; print(platform.machine())")
log "🐍 가상환경 파이썬 정보:"
python3 --version
echo "   Architecture: $PY_ARCH"

log "⬇️  라이브러리 설치..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

log "🏗️  PyInstaller 빌드 시작..."
pyinstaller --clean --noconfirm \
    --distpath ./dist_arm64 \
    --workpath ./build_arm64 \
    YouTube_Downloader_Pro.spec

log "🎉 빌드 완료!"
log "📂 결과물 위치: dist_arm64/YoutubeALL_downloader.app"
log "💡 이 앱은 Apple Silicon Mac 네이티브입니다."
