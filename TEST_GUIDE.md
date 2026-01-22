# 수정 사항 테스트 가이드

## 현재 상황
- 아카이브 파일(`.download_archive.txt`)에 **78개 영상 ID** 기록됨
- 이미 다운로드한 영상은 자동으로 건너뛰기 때문에 경고 메시지를 볼 수 없음
- 새로운 영상을 다운로드할 때만 수정 효과 확인 가능

## 테스트 방법

### 방법 1: 단일 영상으로 테스트 (추천)
아카이브에 없는 새로운 영상 하나로 테스트:

1. 앱 실행
2. **"단일 동영상"** 탭 선택
3. 다른 채널의 영상 URL 입력 (예: 아무 유튜브 영상)
4. 다운로드 시도
5. **상세 로그** 확인 → JavaScript/SABR 경고가 **사라졌는지** 확인

### 방법 2: 아카이브 백업 후 재다운로드
기존 다운로드를 다시 시도하여 테스트:

```bash
# 1. 아카이브 백업
cp .download_archive.txt .download_archive.txt.backup

# 2. 아카이브 삭제 (또는 일부 ID만 삭제)
rm .download_archive.txt

# 3. 앱에서 다운로드 시도
# 4. 로그 확인 - 경고 메시지가 사라졌는지 확인

# 5. 테스트 완료 후 복원 (선택사항)
mv .download_archive.txt.backup .download_archive.txt
```

### 방법 3: 새 영상 기다리기
채널에서 새로운 영상이 업로드되면 자동으로 테스트됨:
- 다음에 "전체 동영상 다운로드" 실행 시
- 새 영상 다운로드 과정에서 경고가 **나타나지 않음**

## 예상 결과

### ✅ 수정 전 (기존)
```
WARNING: [youtube] No supported JavaScript runtime could be found
WARNING: [youtube] Some web_safari client https formats have been skipped
```

### ✅ 수정 후 (현재)
```
[youtube] Extracting URL: https://www.youtube.com/watch?v=xxxxx
[youtube] xxxxx: Downloading android player API JSON
[download] Destination: ...
download: 1024000/10240000|1.5MiB/s|5s|10%
```

**경고 메시지 없이** 깔끔하게 다운로드됨!

## 로그에서 확인할 포인트

### 좋은 신호 ✅
- `Downloading android player API JSON` - Android 클라이언트 사용 중
- `Downloading web player API JSON` - Web 클라이언트 fallback
- JavaScript runtime 경고 **없음**
- SABR streaming 경고 **없음**

### 나쁜 신호 ❌
- `WARNING: No supported JavaScript runtime`
- `WARNING: Some web_safari client https formats have been skipped`
- 다운로드 실패

## 빠른 테스트 명령어

```bash
# 현재 디렉토리에서
cd /Users/sunguk/Desktop/youtubeDown

# yt-dlp 직접 테스트 (가상환경 활성화 후)
source venv_intel/bin/activate

# 테스트 다운로드 (짧은 영상으로)
~/.youtube_downloader_bin/yt-dlp \
  --extractor-args 'youtube:player_client=android,web;player_skip=webpage,configs' \
  -f 'bestvideo[height<=720]+bestaudio/best' \
  --newline \
  https://www.youtube.com/watch?v=jNQXAC9IVRw
```

이렇게 하면 경고 없이 다운로드되는 것을 직접 확인할 수 있습니다!
