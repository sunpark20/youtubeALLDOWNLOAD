#!/bin/bash
# 현재 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 및 Streamlit 앱 실행
source venv/bin/activate
streamlit run app.py
