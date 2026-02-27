"""
API Routes

FastAPI route handlers for all endpoints
"""

import logging
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
from services.downloader import YouTubeDownloader
from services.duplicate_filter import DuplicateFilter
from services.updater import YtdlpUpdater
from utils.config import Config
from utils.validators import is_valid_youtube_url, normalize_input, extract_video_id, extract_playlist_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Service instances (will be initialized with API key)
youtube_service: YouTubeAPIService = None
downloader = YouTubeDownloader()
duplicate_filter = DuplicateFilter()
updater = YtdlpUpdater()


def initialize_services(api_key: str = None):
    """Initialize services with API key"""
    global youtube_service

    api_key = api_key or Config.YOUTUBE_API_KEY

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

        logger.info("YouTube API key updated via settings")
        return APIKeyResponse(
            success=True,
            has_api_key=True,
            message="API 키가 성공적으로 설정되었습니다."
        )
    except Exception as e:
        logger.error(f"Failed to set API key: {e}")
        raise HTTPException(status_code=400, detail=f"API 키 설정 실패: {e}")


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
                channel_id = youtube_service.get_channel_id_from_username(request.url)

            if channel_id:
                logger.info(f"Analyzing channel via API: {channel_id}")
                videos = youtube_service.get_channel_videos(channel_id, request.max_videos)
            else:
                use_fallback = True

        if use_fallback:
            # Fallback to yt-dlp
            logger.info(f"Using yt-dlp fallback for channel analysis: {request.url}")
            videos, channel_meta = downloader.get_channel_videos(request.url, request.max_videos)
            channel_name = channel_meta.get('channel', '')

            # Extract channel_id from URL for download path
            channel_id = YouTubeAPIService.extract_channel_id(request.url) or "unknown_channel"

        if not videos:
            return ChannelAnalyzeResponse(
                success=True,
                channel_id=channel_id,
                message="No videos found in channel"
            )

        total_videos = len(videos)

        # Deduplicate
        videos = duplicate_filter.deduplicate_video_ids(videos)
        unique_videos = len(videos)
        duplicates_removed = total_videos - unique_videos

        # Check for already downloaded
        download_path = Config.get_download_path(channel_id)
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
        if request.include_playlists and youtube_service and channel_id:
            playlist_data = youtube_service.get_channel_playlists(channel_id)
            playlists = [
                PlaylistInfo(id=p['id'], title=p['title'], video_count=0)
                for p in playlist_data
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
            playlists=playlists,
            message=f"Found {to_download} videos to download (via {source})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing channel: {e}")
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
            except Exception as e:
                logger.warning(f"API playlist fetch failed, falling back to yt-dlp: {e}")
                use_fallback = True

        if use_fallback:
            logger.info(f"Using yt-dlp fallback for playlist analysis: {request.url}")
            videos, playlist_meta = downloader.get_playlist_videos(request.url, request.max_videos)

        playlist_name = playlist_meta.get('playlist_title', '') if use_fallback else ''
        channel_name = playlist_meta.get('channel', '') if use_fallback else ''

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
        download_path = Config.get_download_path(playlist_id or "unknown_playlist")
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


@router.post("/download/start")
async def start_download(request: DownloadExtractRequest):
    """
    Server-side download: yt-dlp로 파일을 직접 다운로드하여 저장
    """
    try:
        logger.info(f"Starting server-side download for: {request.video_id} ({request.quality})")

        # 채널명/플레이리스트명 폴더 구조 구성
        output_dir = str(Config.DOWNLOADS_DIR)
        if request.channel_name:
            output_dir = str(Config.DOWNLOADS_DIR / request.channel_name)
            if request.playlist_name:
                output_dir = str(Config.DOWNLOADS_DIR / request.channel_name / request.playlist_name)

        filepath = await asyncio.to_thread(
            downloader.download_video, request.video_id, request.quality, output_dir
        )

        if filepath:
            return {"success": True, "message": "다운로드 완료", "filepath": filepath}
        else:
            raise HTTPException(status_code=500, detail="다운로드 실패")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in server-side download: {e}")
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
