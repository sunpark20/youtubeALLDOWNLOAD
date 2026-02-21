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
    VideoInfo, PlaylistInfo
)
from services.youtube_api import YouTubeAPIService
from services.downloader import YouTubeDownloader
from services.duplicate_filter import DuplicateFilter
from services.updater import YtdlpUpdater
from utils.config import Config
from utils.validators import is_valid_youtube_url, extract_video_id

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
    if not youtube_service:
        raise HTTPException(status_code=503, detail="YouTube API not configured")

    # Validate URL
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        # Extract channel ID
        channel_id = youtube_service.extract_channel_id(request.url)

        if not channel_id:
            # Try to get from username
            channel_id = youtube_service.get_channel_id_from_username(request.url)

        if not channel_id:
            raise HTTPException(status_code=400, detail="Could not extract channel ID")

        logger.info(f"Analyzing channel: {channel_id}")

        # Get all videos
        videos = youtube_service.get_channel_videos(channel_id, request.max_videos)

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

        # Get playlists if requested
        playlists = []
        if request.include_playlists:
            playlist_data = youtube_service.get_channel_playlists(channel_id)
            playlists = [
                PlaylistInfo(id=p['id'], title=p['title'], video_count=0)
                for p in playlist_data
            ]

        return ChannelAnalyzeResponse(
            success=True,
            channel_id=channel_id,
            total_videos=total_videos,
            unique_videos=unique_videos,
            duplicates_removed=duplicates_removed,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            playlists=playlists,
            message=f"Found {to_download} videos to download"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlist/analyze", response_model=PlaylistAnalyzeResponse)
async def analyze_playlist(request: PlaylistAnalyzeRequest):
    """Analyze a YouTube playlist"""
    if not youtube_service:
        raise HTTPException(status_code=503, detail="YouTube API not configured")

    # Implementation similar to channel analysis
    # TODO: Complete implementation

    return PlaylistAnalyzeResponse(
        success=False,
        message="Playlist analysis not yet implemented"
    )


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
