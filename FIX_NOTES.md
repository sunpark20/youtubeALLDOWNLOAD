# YouTube 다운로더 수정 사항 (2026.01.17)

## 🔧 문제점
"모든 영상 다운로드" 시 발생하던 2가지 주요 경고:

1. **JavaScript Runtime 경고**
   ```
   WARNING: No supported JavaScript runtime could be found
   ```

2. **SABR 스트리밍 경고**
   ```
   WARNING: Some web_safari client https formats have been skipped as they are missing a url. 
   YouTube is forcing SABR streaming for this client.
   ```

## ✅ 해결 방법

### 1. JavaScript Runtime 문제 해결
- **이전**: `--js-runtimes node` 옵션 사용 (node가 없으면 경고 발생)
- **수정**: Android 클라이언트를 우선 사용하여 JS 런타임 불필요
  ```python
  '--extractor-args', 'youtube:player_client=android,web;player_skip=webpage,configs'
  ```

### 2. SABR 스트리밍 문제 해결
- **원인**: YouTube가 일부 클라이언트(web_safari 등)에 대해 SABR 스트리밍을 강제하면서 일부 URL 누락
- **해결**: Android 클라이언트를 우선 사용하여 SABR 문제 우회
- **추가**: `player_skip=webpage,configs`로 불필요한 웹페이지 파싱 제거 → 더 빠르고 안정적

### 3. 포맷 선택 개선
더 유연한 fallback 옵션 제공:
```python
# MP4 (720p~1080p)
'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best'

# MKV (최고화질)
'bestvideo+bestaudio/best'
```

## 📋 변경된 파일
- `downloader.py`: 핵심 다운로드 로직 개선

## 🚀 사용 방법
변경 사항은 자동으로 적용됩니다. 앱을 실행하면 됩니다:

```bash
# 가상환경 활성화 (Intel Mac)
source venv_intel/bin/activate

# 앱 실행
streamlit run app.py
```

또는:
```bash
./run_app.sh
```

## 📝 기술적 세부사항

### Android 클라이언트 사용의 장점
1. **JavaScript 불필요**: Android 클라이언트는 네이티브 API만 사용
2. **SABR 우회**: Android 클라이언트는 SABR 제약 없음
3. **빠른 처리**: 웹페이지 파싱 건너뛰기
4. **높은 호환성**: 대부분의 YouTube 영상에서 작동

### Fallback 체인
다운로드가 실패할 경우 자동으로 다음 옵션 시도:
1. MP4 1080p 이하 + M4A 오디오
2. 1080p 이하 비디오 + 최고 오디오
3. 최고 MP4 영상
4. 최고 품질 (어떤 포맷이든)

## 🎯 예상 효과
- ✅ JavaScript 런타임 경고 제거
- ✅ SABR 스트리밍 경고 제거
- ✅ 다운로드 성공률 향상
- ✅ 다운로드 속도 개선
- ✅ 더 안정적인 대용량 플레이리스트 다운로드

## 📚 참고 자료
- yt-dlp 공식 문서: https://github.com/yt-dlp/yt-dlp
- YouTube 클라이언트 이슈: https://github.com/yt-dlp/yt-dlp/issues/12482
- Extractor Arguments: https://github.com/yt-dlp/yt-dlp#youtube
