"""
Pydantic Models

Request and response models for API endpoints
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


# Request Models

class ChannelAnalyzeRequest(BaseModel):
    """Request to analyze a YouTube channel"""
    url: str = Field(..., description="YouTube channel URL")
    include_playlists: bool = Field(default=False, description="Include playlist organization")
    max_videos: int = Field(default=500, description="Maximum videos to fetch")


class PlaylistAnalyzeRequest(BaseModel):
    """Request to analyze a YouTube playlist"""
    url: str = Field(..., description="YouTube playlist URL")
    max_videos: int = Field(default=500, description="Maximum videos to fetch")


class DownloadExtractRequest(BaseModel):
    """Request to extract download URL for a video"""
    video_id: str = Field(..., description="YouTube video ID")
    quality: str = Field(default="720p", description="Preferred quality (360p, 720p, 1080p, audio)")


# Response Models

class VideoInfo(BaseModel):
    """Video information"""
    id: str
    title: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    published_at: Optional[str] = None


class PlaylistInfo(BaseModel):
    """Playlist information"""
    id: str
    title: str
    video_count: int


class ChannelAnalyzeResponse(BaseModel):
    """Response for channel analysis"""
    success: bool
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    total_videos: int = 0
    unique_videos: int = 0
    duplicates_removed: int = 0
    already_downloaded: int = 0
    to_download: int = 0
    videos: List[VideoInfo] = []
    playlists: List[PlaylistInfo] = []
    message: Optional[str] = None


class PlaylistAnalyzeResponse(BaseModel):
    """Response for playlist analysis"""
    success: bool
    playlist_id: Optional[str] = None
    playlist_name: Optional[str] = None
    total_videos: int = 0
    unique_videos: int = 0
    duplicates_removed: int = 0
    already_downloaded: int = 0
    to_download: int = 0
    videos: List[VideoInfo] = []
    message: Optional[str] = None


class DownloadFormat(BaseModel):
    """Download format information"""
    quality: str
    url: str
    ext: str
    filesize: Optional[int] = None


class DownloadExtractResponse(BaseModel):
    """Response for download URL extraction"""
    success: bool
    video_id: str
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    formats: Dict[str, str] = {}  # quality -> URL mapping
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    app_name: str
    version: str
    ytdlp_version: Optional[str] = None


class UpdateResponse(BaseModel):
    """Update check/execute response"""
    success: bool
    current_version: Optional[str] = None
    latest_version: Optional[str] = None
    message: str


class APIKeyRequest(BaseModel):
    """Request to set YouTube API key"""
    api_key: str = Field(..., description="YouTube Data API v3 key")


class APIKeyResponse(BaseModel):
    """Response for API key operations"""
    success: bool
    has_api_key: bool = False
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[str] = None
