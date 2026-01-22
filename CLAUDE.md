# YouTube Downloader Pro 프로젝트

## 프로젝트 개요
Streamlit 기반 YouTube 비디오 다운로더. yt-dlp를 사용하여 채널, 재생목록, 개별 영상 다운로드를 지원합니다.

## 핵심 아키텍처

### 주요 파일
- **app.py**: Streamlit UI, 탭 구조, 사용자 입력 처리
- **downloader.py**: yt-dlp 실행, 진행률 파싱, 실시간 상태 업데이트
- **utils.py**: 설정 관리, ffmpeg/yt-dlp 경로 관리, 아카이브 동기화

### 기술 스택
- **Frontend**: Streamlit
- **다운로드 엔진**: yt-dlp (자동 설치/업데이트)
- **비디오 처리**: ffmpeg
- **패키징**: PyInstaller (macOS .app 생성)

## 다운로드 모드 (4가지)
1. **전체 동영상 다운로드**: 채널의 모든 영상
2. **전체 재생목록 동영상**: 채널의 모든 재생목록을 폴더별로
3. **개별 플레이 리스트**: 특정 재생목록 URL
4. **단일 동영상**: 개별 영상

## 파일명 규칙 (절대 변경 금지)
```
%(upload_date)s - %(title)s [%(id)s].%(ext)s
```
예: `20231225 - 영상제목 [AbCdEfGh].mp4`

## 아카이브 관리
- 각 다운로드 폴더마다 `.download_archive.txt` 파일로 이력 관리
- 다운로드 시작 전 실제 파일과 아카이브 동기화 (`sync_archive()`)
- 개별 영상 모드는 아카이브 무시하고 강제 다운로드

## yt-dlp 설정 (중요)
### Android 클라이언트 우선 사용
```python
'--extractor-args', 'youtube:player_client=ios,android,web;player_skip=webpage,configs'
```
- JavaScript 런타임 불필요
- SABR 스트리밍 문제 우회
- 빠르고 안정적인 다운로드

### 포맷 선택
- **MP4 (모바일용)**: `bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]`
- **MKV (최고화질)**: `bestvideo+bestaudio`
- **MP3 (음성)**: `--extract-audio --audio-format mp3 --audio-quality 0`

## 환경 구성

### 개발 환경
```bash
# Apple Silicon (ARM64)
source venv_arm64/bin/activate
streamlit run app.py

# Intel Mac
source venv_intel/bin/activate
streamlit run app.py
```

### 빌드
```bash
# Apple Silicon 네이티브 빌드
./build_arm64.sh

# Intel Mac 빌드 (Rosetta 통해 실행 가능)
./build_intel.sh
./package_intel_dmg.sh
```

## 설정 파일 위치
- **사용자 설정**: `~/.youtube_downloader_config.json`
- **바이너리**: `~/.youtube_downloader_bin/yt-dlp`

## 최근 해결한 문제
1. JavaScript Runtime 경고 → Android 클라이언트 사용으로 해결
2. SABR 스트리밍 경고 → iOS/Android 클라이언트 우선 사용으로 해결
3. 대용량 재생목록 다운로드 안정성 개선

## 코딩 컨벤션
- 주석 최소화 (사용자용 주석 금지)
- 단순함 유지
- 성능 최적화 우선
- Streamlit 리렌더링 최소화

## 테스트 방법
1. 단일 영상 다운로드 테스트
2. 쇼츠 제외 필터 테스트 (3분 이하)
3. 아카이브 동기화 테스트
4. yt-dlp 업데이트 테스트
