#!/bin/bash
# 현재 스크립트 위치로 이동
cd "$(dirname "$0")"

echo "--------------------------------------------------"
echo "🛡️  YouTube Downloader 보안 경고(손상됨) 해결 스크립트"
echo "--------------------------------------------------"

APP_PATH="/Applications/YoutubeALL_downloader.app"

if [ -d "$APP_PATH" ]; then
    echo "📍 앱 위치 확인: $APP_PATH"
    # 격리 속성 및 확장 속성 제거
    xattr -cr "$APP_PATH"
    echo ""
    echo "✅ 처리 완료! 이제 앱을 더블클릭해서 실행해 보세요."
    echo "   (여전히 보안 경고가 뜨면 '우클릭 > 열기'를 사용하세요.)"
else
    echo "❌ 오류: 앱이 /Applications 폴더에 없습니다."
    echo "   먼저 앱을 '응용 프로그램(Applications)' 폴더로 옮긴 후"
    echo "   이 스크립트를 다시 실행해 주세요."
fi

echo "--------------------------------------------------"
echo "이 창은 닫으셔도 됩니다. (3초 후 자동 종료)"
sleep 3
