#!/bin/bash
set -e

# 로그 출력 함수
log() {
    echo -e "\n[Intel-Build] $1"
}

# 1. 아키텍처 확인 및 x86_64 모드로 재실행
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
    log "현재 아키텍처: $ARCH. Intel(x86_64) 모드로 전환합니다..."
    exec arch -x86_64 /bin/bash "$0" "$@"
fi

log "✅ Intel(x86_64) 모드 진입 성공."

# 프로젝트 디렉토리로 이동 (스크립트 위치 기준)
cd "$(dirname "$0")"

# 2. 가상환경 설정
VENV_NAME="venv_intel"

if [ ! -d "$VENV_NAME" ]; then
    log "🔨 인텔용 가상환경($VENV_NAME) 생성 중..."
    # 시스템 기본 python3 (/usr/bin/python3)는 Universal Binary이므로 이를 사용
    # 명시적으로 arch -x86_64를 붙여서 venv 생성
    arch -x86_64 /usr/bin/python3 -m venv "$VENV_NAME"
else
    log "♻️  기존 가상환경($VENV_NAME) 사용"
fi

# 3. 가상환경 활성화
source "$VENV_NAME/bin/activate"

# 검증 (venv 내부 python이 인텔 모드로 도는지 확인)
# 주의: venv의 python은 심볼릭 링크일 수 있으므로, 실행 시 arch -x86_64 환경 내부에 있어야 함.
# 현재 쉘이 이미 arch -x86_64 상태이므로 그냥 실행해도 x86_64여야 함.
PY_ARCH=$(python3 -c "import platform; print(platform.machine())")
log "🐍 가상환경 파이썬 정보:"
python3 --version
echo "   Architecture: $PY_ARCH"


# 4. 의존성 설치
log "⬇️  라이브러리 설치 (streamlit, requests, pyinstaller)..."
# pip 업그레이드 및 라이브러리 설치 (조용하게)
pip install --quiet --upgrade pip
pip install --quiet streamlit requests pyinstaller

# 5. 빌드 실행
log "🏗️  PyInstaller 빌드 시작..."
# 기존 dist/build 폴더와 섞이지 않도록 경로 지정
# --distpath: 결과물이 저장될 폴더 (dist_intel)
# --workpath: 임시 파일이 저장될 폴더 (build_intel)
pyinstaller --clean --noconfirm \
    --distpath ./dist_intel \
    --workpath ./build_intel \
    YouTube_Downloader_Pro.spec

log "🎉 빌드 완료!"
log "📂 결과물 위치: dist_intel/YoutubeALL_downloader.app"
log "💡 주의: 이 앱은 Intel Mac용입니다. 실리콘 맥에서는 로제타를 통해 실행됩니다."
