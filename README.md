## 업데이트

구버전 윈도우에서 webView2 가 없어 실행이 안되는 문제 - 앱시작시 webview2설치 추가
현재 제 pc로 정상 실행 확인 빌드 v1.2.7 - 실리콘맥(m1), 윈도우11(64bit)최신팩 
커뮤니티 댓글은 제가 못볼수도 있습니다.

## 오류수정요청 

다운로드시 빌드버전 명시 v1.2.x  
실행안되는 증상 상세히(프로그램 눌렀는데 안떠요 / 떳다가 바로 사라졌어요 / 어떤 오류가 났어요 등)
사용하시는 pc의 스펙 찍어주기
sun.park20@gmail.com 이메일로 요청드립니다!



## 소개

제가 쓰려고 만들었어요. 4K Downloader 영구 라이센스 유료로 쓰고 있었는데, 이놈들이 구버전 서비스 종료하고 신버전을 만들더라구요. 열받아!!!(아주 과거임)

나는 바다에서 근무합니다. 오프라인 환경에 한번에 동영상을 다운받아가요.
여행유튜브 동영상이 아주 많기 때문에 순서대로 보기 쉽지 않아요.
그래서 다운받아지면 `260311_영상제목` 같이 정렬되게 만들었어요.


## 다운로드

https://github.com/sunpark20/YT-Chita/releases


## 주요 기능

- **채널 전체 다운로드** — 채널의 모든 영상을 한번에
- **재생목록 다운로드** — 단일 재생목록 또는 채널의 모든 재생목록
- **개별 다운로드** — 단일 URL 입력으로 1개도 다운로드
- **화질 선택** — 음원만(m4a) / 360p / 720p / 1080p / 최고화질


## 한계

- **실리콘맥 우선** — 제게 인텔맥과 윈도우는 없기 때문에 테스트가 너무 어렵습니다.
댓글이나 이메일로 문제 보내주시면, 시간날 때 개선하겠습니다.(현재 윈도우버전은 yt-dlp 업데이트 안되는 상황이라 수동으로 잡아줘야해서 자주 안될겁니다.ㅜㅜ)
- **치명적 버그** — yt-dlp 윈도우에서 업데이트가 안됨.
- **동작 문제없으나 고칠점** —  1.업데이트 플로우를 어떻게 개선함???? 인터넷 다운로드, 2.자막 넣기 빼기

   
## 포맷

- **음원(m4a)**: AAC 원본 그대로 저장(변환 없음)
- **360p / 720p / 1080p**: H.264 우선, 없으면 다른 코덱으로 대체
- **최고화질**: 코덱 무관, 최고 해상도 다운로드 (4K VP9/AV1 등)


## 참고

- API 키 추가하면, 오류 덜 나고 영상 분석이 빨라집니다. 100개 이상 영상 받을 때 추천


## Disclaimer

이 앱은 개인 오프라인 시청, 백업 등 합법적 용도를 위해 만들어졌습니다. 저작권이 있는 콘텐츠의 무단 배포는 사용자의 책임입니다.


## License

이 프로젝트는 [The Unlicense](https://unlicense.org/)로 배포됩니다.

### Open Source Libraries

| 라이브러리 | 라이선스 |
|-----------|---------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense |
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1 / GPL |
| [FastAPI](https://github.com/tiangolo/fastapi) | MIT |
| [pywebview](https://github.com/nicegui-kr/pywebview) | BSD-3-Clause |
| [uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | GPL-2.0 (빌드 도구) |
