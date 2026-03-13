"""
API Routes

FastAPI route handlers for all endpoints
"""

import logging
from collections import Counter
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json

from .models import (
    ChannelAnalyzeRequest, ChannelAnalyzeResponse,
    PlaylistAnalyzeRequest, PlaylistAnalyzeResponse,
    DownloadExtractRequest, DownloadExtractResponse,
    HealthResponse, UpdateResponse, ErrorResponse,
    APIKeyRequest, APIKeyResponse,
    VideoInfo, PlaylistInfo
)
from services.youtube_api import YouTubeAPIService
from services.downloader import YTBulkDownloader
from services.duplicate_filter import DuplicateFilter
from services.updater import YtdlpUpdater
from utils.config import Config
from utils.validators import is_valid_youtube_url, normalize_input, extract_video_id, extract_playlist_id
from utils.key_manager import load_api_key_from_file, save_api_key_to_file, delete_api_key_from_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Service instances (will be initialized with API key)
youtube_service: YouTubeAPIService = None
downloader = YTBulkDownloader()
duplicate_filter = DuplicateFilter()
updater = YtdlpUpdater()


def initialize_services(api_key: str = None):
    """Initialize services with API key"""
    global youtube_service

    # Try config first, then saved file
    api_key = api_key or Config.YOUTUBE_API_KEY or load_api_key_from_file()

    if api_key:
        youtube_service = YouTubeAPIService(api_key)
        logger.info("YouTube API service initialized")
    else:
        logger.warning("YouTube API key not set - some features will be limited")


@router.get("/settings", response_model=APIKeyResponse)
async def get_settings():
    """Get current settings (API key status)"""
    has_key = youtube_service is not None
    return APIKeyResponse(
        success=True,
        has_api_key=has_key,
        message="API 키가 설정되어 있습니다." if has_key else "API 키가 설정되지 않았습니다. (yt-dlp 폴백 사용)"
    )


@router.post("/settings/api-key", response_model=APIKeyResponse)
async def set_api_key(request: APIKeyRequest):
    """Set YouTube Data API key at runtime"""
    global youtube_service

    api_key = request.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API 키가 비어있습니다.")

    try:
        if youtube_service:
            youtube_service.set_api_key(api_key)
        else:
            youtube_service = YouTubeAPIService(api_key)

        save_api_key_to_file(api_key)

        logger.info("YouTube API key updated via settings")
        return APIKeyResponse(
            success=True,
            has_api_key=True,
            message="API 키가 성공적으로 설정되었습니다."
        )
    except Exception as e:
        logger.error(f"Failed to set API key: {e}")
        raise HTTPException(status_code=400, detail=f"API 키 설정 실패: {e}")


@router.delete("/settings/api-key", response_model=APIKeyResponse)
async def delete_api_key():
    """Remove YouTube Data API key at runtime"""
    global youtube_service
    youtube_service = None
    delete_api_key_from_file()
    logger.info("YouTube API key removed via settings")
    return APIKeyResponse(
        success=True,
        has_api_key=False,
        message="API 키가 삭제되어 yt-dlp 모드로 전환되었습니다."
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    ytdlp_version = updater.get_current_version()

    return HealthResponse(
        status="healthy",
        app_name=Config.APP_NAME,
        version=Config.APP_VERSION,
        ytdlp_version=ytdlp_version
    )


@router.post("/updater/check", response_model=UpdateResponse)
async def check_update():
    """Check for yt-dlp updates"""
    current = updater.get_current_version()

    return UpdateResponse(
        success=True,
        current_version=current,
        message=f"Current version: {current}"
    )


@router.post("/updater/update", response_model=UpdateResponse)
async def perform_update():
    """Update yt-dlp to latest version"""
    success, message = updater.check_and_update()

    return UpdateResponse(
        success=success,
        current_version=updater.current_version,
        latest_version=updater.latest_version,
        message=message
    )


@router.post("/channel/analyze", response_model=ChannelAnalyzeResponse)
async def analyze_channel(request: ChannelAnalyzeRequest):
    """
    Analyze a YouTube channel and get all videos

    Steps:
    1. Extract channel ID from URL
    2. Get all videos from channel
    3. Deduplicate videos
    4. Check for already downloaded files
    5. Return analysis results
    """
    # Normalize and validate URL
    request.url = normalize_input(request.url)
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        channel_id = None
        channel_name = ''
        videos = []
        use_fallback = not youtube_service

        if not use_fallback:
            # Try YouTube Data API first
            channel_id = youtube_service.extract_channel_id(request.url)

            if not channel_id:
                # Extract username and fetch channel ID
                username = youtube_service.extract_username(request.url)
                if username:
                    channel_id = youtube_service.get_channel_id_from_username(username)

            if channel_id:
                channel_name = youtube_service.get_channel_title(channel_id) or channel_id
                logger.info(f"Analyzing channel via API: {channel_id} ({channel_name})")
                videos = youtube_service.get_channel_videos(channel_id, request.max_videos)
            else:
                use_fallback = True

        if use_fallback:
            # Fallback to yt-dlp
            logger.info(f"Using yt-dlp fallback for channel analysis: {request.url}")
            videos, channel_meta = downloader.get_channel_videos(request.url, request.max_videos)
            channel_name = channel_meta.get('channel', '')

            # Extract channel_id from URL for download path
            channel_id = YouTubeAPIService.extract_channel_id(request.url) or YouTubeAPIService.extract_username(request.url) or "unknown_channel"

        if not videos:
            return ChannelAnalyzeResponse(
                success=True,
                channel_id=channel_id,
                message="No videos found in channel"
            )

        # 멤버십 전용 영상 필터링 (availability 필드 + 제목 키워드)
        membership_avail = {'subscriber_only', 'needs_auth', 'premium_only'}
        membership_title_kw = ['멤버십', '멤버쉽', '회원 전용', 'membership', 'members only']
        videos = [
            v for v in videos
            if (v.get('availability') or '') not in membership_avail
            and not any(kw in (v.get('title') or '').lower() for kw in membership_title_kw)
        ]

        # Filter Shorts (≤180s) when using API and include_shorts is False
        if not request.include_shorts and not use_fallback:
            videos = [v for v in videos if (v.get('duration') or 999) > 180]

        total_videos = len(videos)

        # Deduplicate
        videos = duplicate_filter.deduplicate_video_ids(videos)
        unique_videos = len(videos)
        duplicates_removed = total_videos - unique_videos

        # Check for already downloaded
        safe_channel_name = channel_name or channel_id or "Unknown Channel"
        download_path = Config.get_download_path(safe_channel_name)
        videos = duplicate_filter.filter_already_downloaded(videos, str(download_path))
        to_download = len(videos)
        already_downloaded = unique_videos - to_download

        # Convert to response format
        video_infos = [
            VideoInfo(
                id=v['id'],
                title=v['title'],
                published_at=v.get('publishedAt')
            )
            for v in videos
        ]

        # Get playlists if requested (only with API)
        playlists = []

        source = "yt-dlp" if use_fallback else "YouTube API"
        return ChannelAnalyzeResponse(
            success=True,
            channel_id=channel_id,
            channel_name=channel_name or None,
            total_videos=total_videos,
            unique_videos=unique_videos,
            duplicates_removed=duplicates_removed,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            playlists=playlists,
            message=f"Found {to_download} videos to download (via {source})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/channel/playlists/analyze", response_model=ChannelAnalyzeResponse)
async def analyze_channel_playlists(request: ChannelAnalyzeRequest):
    """Analyze a YouTube channel's playlists and get all videos grouped by playlist"""
    request.url = normalize_input(request.url)
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        channel_id = None
        channel_name = ''
        videos_list = []
        use_fallback = not youtube_service

        if not use_fallback:
            channel_id = youtube_service.extract_channel_id(request.url)
            if not channel_id:
                username = youtube_service.extract_username(request.url)
                if username:
                    channel_id = youtube_service.get_channel_id_from_username(username)
            
            if channel_id:
                channel_name = youtube_service.get_channel_title(channel_id) or channel_id
                logger.info(f"Analyzing channel playlists via API: {channel_id} ({channel_name})")
                # Fetch all playlists
                playlists = youtube_service.get_channel_playlists(channel_id)

                # 멤버십 전용 재생목록 필터링
                membership_keywords = ['멤버십', '멤버쉽', 'membership', 'members only', 'members-only']
                playlists = [
                    pl for pl in playlists
                    if not any(kw in pl['title'].lower() for kw in membership_keywords)
                ]

                # 같은 이름 재생목록 → 상위 폴더/하위 번호 폴더 구조
                name_counts = Counter(pl['title'] for pl in playlists)
                name_indices = {}
                for pl in playlists:
                    name = pl['title']
                    if name_counts[name] > 1:
                        idx = name_indices.get(name, 0) + 1
                        name_indices[name] = idx
                        pl['folder_name'] = f"{name}/{name} ({idx})"
                    else:
                        pl['folder_name'] = name

                for pl in playlists:
                    pl_videos = youtube_service.get_playlist_videos(pl['id'], request.max_videos)
                    for v in pl_videos:
                        videos_list.append({
                            'id': v['id'],
                            'title': v['title'],
                            'publishedAt': v.get('publishedAt'),
                            'playlist_name': pl['folder_name']
                        })
            else:
                use_fallback = True

        if use_fallback:
            # Fallback for playlists is complex with yt-dlp, we will try to use yt-dlp on the /playlists URL directly
            # which usually yields playlists. Then we extract videos.
            logger.info(f"Using yt-dlp fallback for channel playlists analysis: {request.url}")
            
            import yt_dlp
            import re as _re
            # Make sure url ends with /playlists
            url = request.url.rstrip('/')
            if not url.endswith('/playlists'):
                if url.endswith('/videos'):
                    url = url[:-7]
                url += '/playlists'

            # 비-ASCII 핸들(@한글이름) → channel ID로 변환
            _handle_match = _re.search(r'/@([^/]+)', url)
            if _handle_match:
                _handle = _handle_match.group(1)
                if any(ord(c) > 127 for c in _handle):
                    _cid = downloader._resolve_handle_to_channel_id(_handle)
                    if _cid:
                        url = f"https://www.youtube.com/channel/{_cid}/playlists"
                        logger.info(f"Resolved non-ASCII handle @{_handle} → {_cid}")
                
            ydl_opts = {'quiet': True, 'extract_flat': True}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    channel_name = info.get('channel', '') or info.get('uploader', '')
                    channel_id = info.get('channel_id', 'unknown_channel')
                    
                    entries = list(info.get('entries', []))

                    # 멤버십 전용 재생목록 필터링
                    membership_keywords = ['멤버십', '멤버쉽', 'membership', 'members only', 'members-only']
                    entries = [
                        e for e in entries
                        if e and not any(kw in (e.get('title') or '').lower() for kw in membership_keywords)
                    ]

                    # 같은 이름 재생목록 → 상위 폴더/하위 번호 폴더 구조
                    pl_titles = [e.get('title', 'Unknown Playlist') for e in entries if e]
                    fb_name_counts = Counter(pl_titles)
                    fb_name_indices = {}

                    for pl_entry in entries:
                        if not pl_entry:
                            continue
                        pl_title = pl_entry.get('title', 'Unknown Playlist')
                        if fb_name_counts[pl_title] > 1:
                            idx = fb_name_indices.get(pl_title, 0) + 1
                            fb_name_indices[pl_title] = idx
                            folder_name = f"{pl_title}/{pl_title} ({idx})"
                        else:
                            folder_name = pl_title

                        pl_url = pl_entry.get('url')
                        if pl_url:
                            pl_info = ydl.extract_info(pl_url, download=False)
                            for v_entry in pl_info.get('entries', []):
                                if v_entry and v_entry.get('id'):
                                    # 개별 영상 멤버십 필터 (yt-dlp availability 필드)
                                    avail = (v_entry.get('availability') or '').lower()
                                    if avail in ('subscriber_only', 'needs_auth', 'premium_only'):
                                        logger.info(f"Skipping membership video: {v_entry.get('title')} ({avail})")
                                        continue
                                    videos_list.append({
                                        'id': v_entry['id'],
                                        'title': v_entry.get('title', 'Unknown'),
                                        'playlist_name': folder_name
                                    })
            except Exception as e:
                logger.error(f"yt-dlp fallback failed for playlists: {e}")

        if not videos_list:
            return ChannelAnalyzeResponse(
                success=True,
                channel_id=channel_id,
                message="No playlist videos found"
            )

        total_videos = len(videos_list)

        # Deduplicate - wait, we might have same video in multiple playlists. 
        # If user wants them in separate folders, we SHOULD NOT deduplicate across playlists, 
        # or we only deduplicate exact same video in the exact same playlist.
        # Let's deduplicate by (id, playlist_name)
        unique_vids = []
        seen = set()
        for v in videos_list:
            key = (v['id'], v.get('playlist_name', ''))
            if key not in seen:
                seen.add(key)
                unique_vids.append(v)
                
        videos_list = unique_vids
        unique_videos = len(videos_list)
        duplicates_removed = total_videos - unique_videos

        # Check for already downloaded
        to_download_vids = []
        already_downloaded = 0
        from utils.config import Config
        for v in videos_list:
            safe_chan = channel_name or channel_id or "Unknown Channel"
            safe_pl = v.get('playlist_name') or "Unknown Playlist"
            download_path = Config.get_download_path(safe_chan, safe_pl)
            
            # Check if file exists (duplicate_filter logic for single file)
            # Actually DuplicateFilter expects a list of IDs. We can check manually or use filter.
            # It's easier to use the filter per video.
            res = duplicate_filter.filter_already_downloaded([v], str(download_path))
            if res:
                to_download_vids.append(v)
            else:
                already_downloaded += 1
                
        to_download = len(to_download_vids)

        video_infos = [
            VideoInfo(
                id=v['id'],
                title=v['title'],
                published_at=v.get('publishedAt'),
                playlist_name=v.get('playlist_name')
            )
            for v in to_download_vids
        ]

        source = "yt-dlp" if use_fallback else "YouTube API"
        return ChannelAnalyzeResponse(
            success=True,
            channel_id=channel_id,
            channel_name=channel_name or None,
            total_videos=total_videos,
            unique_videos=unique_videos,
            duplicates_removed=duplicates_removed,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            message=f"Found {to_download} videos to download (via {source})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing channel playlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video/analyze", response_model=ChannelAnalyzeResponse)
async def analyze_video(request: PlaylistAnalyzeRequest):
    """Analyze a single YouTube video URL — returns 1 video, saved to channel root folder"""
    request.url = normalize_input(request.url)
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        video_id = extract_video_id(request.url)
        if not video_id:
            raise HTTPException(status_code=400, detail="동영상 ID를 추출할 수 없습니다.")

        # yt-dlp로 영상 정보 가져오기
        info = await asyncio.to_thread(downloader.get_video_info, video_id)
        if not info:
            raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")

        channel_name = info.get('uploader', '') or 'Unknown Channel'

        # 이미 다운로드 여부 확인 (채널 루트 폴더)
        download_path = Config.get_download_path(channel_name)
        remaining = duplicate_filter.filter_already_downloaded(
            [{'id': video_id, 'title': info['title']}], str(download_path)
        )
        # remaining: 아직 다운로드 안 된 영상 목록 (0개면 이미 받음, 1개면 미다운로드)
        to_download = len(remaining)
        already_downloaded = 1 - to_download

        video_infos = [
            VideoInfo(id=video_id, title=info['title'])
        ] if remaining else []

        return ChannelAnalyzeResponse(
            success=True,
            channel_name=channel_name,
            total_videos=1,
            unique_videos=1,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            message=f"단일 영상 분석 완료"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlist/analyze", response_model=PlaylistAnalyzeResponse)
async def analyze_playlist(request: PlaylistAnalyzeRequest):
    """Analyze a YouTube playlist"""
    request.url = normalize_input(request.url)
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        playlist_id = extract_playlist_id(request.url)
        videos = []
        playlist_meta = {}
        use_fallback = not youtube_service

        if not use_fallback:
            try:
                videos = youtube_service.get_playlist_videos(playlist_id, request.max_videos)
                info = youtube_service.get_playlist_info(playlist_id)
                if info:
                    playlist_meta['playlist_title'] = info.get('title', '')
                    playlist_meta['channel'] = info.get('channelTitle', '')
            except Exception as e:
                logger.warning(f"API playlist fetch failed, falling back to yt-dlp: {e}")
                use_fallback = True

        if use_fallback:
            logger.info(f"Using yt-dlp fallback for playlist analysis: {request.url}")
            videos, playlist_meta = downloader.get_playlist_videos(request.url, request.max_videos)

        playlist_name = playlist_meta.get('playlist_title', '')
        channel_name = playlist_meta.get('channel', '')

        if not videos:
            return PlaylistAnalyzeResponse(
                success=True,
                playlist_id=playlist_id,
                message="No videos found in playlist"
            )

        total_videos = len(videos)

        # Deduplicate
        videos = duplicate_filter.deduplicate_video_ids(videos)
        unique_videos = len(videos)
        duplicates_removed = total_videos - unique_videos

        # Check for already downloaded
        safe_channel_name = channel_name or "Unknown Channel"
        safe_playlist_name = playlist_name or playlist_id or "Unknown Playlist"
        download_path = Config.get_download_path(safe_channel_name, safe_playlist_name)
        videos = duplicate_filter.filter_already_downloaded(videos, str(download_path))
        to_download = len(videos)
        already_downloaded = unique_videos - to_download

        video_infos = [
            VideoInfo(
                id=v['id'],
                title=v['title'],
                published_at=v.get('publishedAt')
            )
            for v in videos
        ]

        source = "yt-dlp" if use_fallback else "YouTube API"
        return PlaylistAnalyzeResponse(
            success=True,
            playlist_id=playlist_id,
            playlist_name=playlist_name or None,
            channel_name=channel_name or None,
            total_videos=total_videos,
            unique_videos=unique_videos,
            duplicates_removed=duplicates_removed,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            message=f"Found {to_download} videos to download (via {source})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/progress/{video_id}")
async def get_download_progress_by_id(video_id: str):
    """Get download progress for a specific video"""
    return downloader.get_progress(video_id) or {}


@router.get("/download/progress")
async def get_download_progress():
    """Get all download progress (backwards compatible)"""
    all_prog = downloader.get_progress()
    if not all_prog:
        return {}
    # 기존 호환: 단일 dict 반환 (가장 최근 활성 항목)
    for vid, prog in all_prog.items():
        if prog.get('status') == 'downloading':
            return prog
    # downloading 없으면 아무거나 반환
    return next(iter(all_prog.values()), {})


@router.post("/download/reset-cancel")
async def reset_cancel():
    """배치 시작 전 취소 플래그 초기화 + 잔여 임시파일 정리"""
    downloader.reset_cancel()
    # 이전 강제 종료로 남은 임시파일 정리 (배치 시작 전 1회, 재귀)
    import glob as _glob
    import os as _os
    base = str(Config.DOWNLOADS_DIR)
    for pattern in ('**/*.part', '**/*.ytdl', '**/*.part-Frag*'):
        for f in _glob.glob(_os.path.join(base, pattern), recursive=True):
            try:
                _os.remove(f)
            except OSError:
                pass
    return {"success": True, "message": "취소 플래그 초기화됨"}


@router.post("/download/cancel")
async def cancel_download():
    """현재 진행 중인 다운로드를 즉시 취소"""
    downloader.request_cancel()
    return {"success": True, "message": "다운로드 중단 요청됨"}


@router.post("/download/start")
async def start_download(request: DownloadExtractRequest):
    """
    Server-side download: yt-dlp로 파일을 직접 다운로드하여 저장
    이미 다운로드된 파일은 스킵 처리
    """
    try:
        logger.info(f"Starting server-side download for: {request.video_id} ({request.quality})")

        # 채널명/플레이리스트명 폴더 구조 구성
        output_dir = str(Config.get_download_path(request.channel_name or "", request.playlist_name or ""))

        # 스킵 체크: 이미 다운로드된 파일인지 확인
        from services.download_archive import get_archive
        archive = get_archive(output_dir)

        if archive.has_video(request.video_id) or duplicate_filter.is_file_downloaded(request.video_id, output_dir):
            logger.info(f"Skipping already downloaded: {request.video_id}")
            return {"success": True, "skipped": True, "message": "이미 다운로드됨 (스킵)"}

        # 실제 다운로드 수행
        filepath = await asyncio.to_thread(
            downloader.download_video, request.video_id, request.quality, output_dir
        )

        if filepath == "CANCELLED":
            return {"success": False, "cancelled": True, "message": "사용자가 다운로드를 중단했습니다."}
        elif filepath == "MEMBERSHIP_SKIP":
            # 멤버십 전용 영상 → 아카이브에 기록하여 다음에 스킵
            archive.add_video(request.video_id)
            return {"success": True, "skipped": True, "message": "멤버십 전용 (스킵)", "reason": "멤버십"}
        elif filepath == "AGE_RESTRICTED_SKIP":
            # 성인인증 필요 영상 → 아카이브에 기록하여 다음에 스킵
            archive.add_video(request.video_id)
            return {"success": True, "skipped": True, "message": "성인제한 (스킵)", "reason": "성인제한"}
        elif filepath:
            # 다운로드 성공 → 아카이브에 기록
            archive.add_video(request.video_id)
            return {"success": True, "skipped": False, "message": "다운로드 완료", "filepath": filepath}
        else:
            raise HTTPException(status_code=500, detail="다운로드 실패")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in server-side download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/open-log-folder")
async def open_log_folder():
    """Open the log folder in the system file manager"""
    import subprocess
    import platform
    import os
    from utils.logger import _get_log_dir

    log_dir = str(_get_log_dir())

    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", log_dir])
        elif system == "Windows":
            os.startfile(log_dir)
        else:
            subprocess.Popen(["xdg-open", log_dir])
        return {"success": True, "path": log_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/open-folder")
async def open_folder(request: dict):
    """Open a folder in the system file manager"""
    import subprocess
    import platform
    import os

    folder_path = request.get("path", "")
    if not folder_path:
        raise HTTPException(status_code=400, detail="경로가 비어있습니다.")

    # Expand ~ to home directory
    folder_path = os.path.expanduser(folder_path)

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=404, detail="폴더가 존재하지 않습니다.")

    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", folder_path])
        elif system == "Windows":
            os.startfile(folder_path)
        else:
            subprocess.Popen(["xdg-open", folder_path])
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download/extract", response_model=DownloadExtractResponse)
async def extract_download_url(request: DownloadExtractRequest):
    """
    Extract direct download URL for a video

    Returns URLs for different quality options
    """
    try:
        logger.info(f"Extracting download URL for: {request.video_id} ({request.quality})")

        # Get download info
        info = downloader.get_download_info(request.video_id)

        if not info:
            raise HTTPException(status_code=404, detail="Video not found or unavailable")

        return DownloadExtractResponse(
            success=True,
            video_id=request.video_id,
            title=info.get('title'),
            thumbnail=info.get('thumbnail'),
            duration=info.get('duration'),
            formats=info.get('formats', {}),
            message="Download URLs extracted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting download URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
