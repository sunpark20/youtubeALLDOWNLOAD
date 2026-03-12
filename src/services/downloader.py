"""
YouTube Downloader Service

Wrapper around yt-dlp for extracting download information
"""

import glob
import logging
import os
import re
import sys
import threading
import yt_dlp
from typing import Dict, List, Optional

from utils.config import Config

logger = logging.getLogger(__name__)


def _get_ffmpeg_location() -> str:
    """Get ffmpeg path — bundled binary in PyInstaller, or system default."""
    is_windows = sys.platform.startswith('win')
    ffmpeg_bin = 'ffmpeg.exe' if is_windows else 'ffmpeg'

    if getattr(sys, 'frozen', False):
        # PyInstaller 빌드 환경
        bundle_dir = os.path.dirname(sys.executable)
        
        # 탐색할 후보 경로들
        candidates = [bundle_dir]
        if not is_windows:
            # macOS 전용 구조 추가
            candidates.extend([
                os.path.join(bundle_dir, '..', 'Frameworks'),
                os.path.join(bundle_dir, '..', 'Resources'),
            ])

        for candidate in candidates:
            ffmpeg_path = os.path.join(candidate, ffmpeg_bin)
            if os.path.isfile(ffmpeg_path):
                # yt-dlp는 파일 경로가 아니라 디렉토리 경로를 원할 때가 많음
                return os.path.abspath(candidate)
    
    return ''  # 시스템 PATH에서 찾음 (이미 PATH에 있는 경우)


class YouTubeDownloader:
    """yt-dlp wrapper for YouTube downloads"""

    def __init__(self):
        ffmpeg_loc = _get_ffmpeg_location()
        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {'youtube': {'lang': ['ko']}},
        }
        if ffmpeg_loc:
            self.ydl_opts_base['ffmpeg_location'] = ffmpeg_loc
        self._progress = {}  # 현재 진행률 데이터
        self._last_total = ''  # 다운로드 완료 시 파일크기 보관 (MP3 변환 후 사용)
        self._cancel_event = threading.Event()

    def request_cancel(self):
        """외부에서 다운로드 취소를 요청"""
        self._cancel_event.set()

    def reset_cancel(self):
        """취소 플래그 초기화"""
        self._cancel_event.clear()

    @staticmethod
    def _strip_ansi(s: str) -> str:
        """Remove ANSI escape sequences from string"""
        return re.sub(r'\x1b\[[0-9;]*m', '', s)

    def _progress_hook(self, d):
        """yt-dlp progress callback"""
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadError("사용자가 다운로드를 중단했습니다.")
        if d['status'] == 'downloading':
            self._progress = {
                'status': 'downloading',
                'percent': self._strip_ansi(d.get('_percent_str', '')).strip(),
                'total': self._strip_ansi(d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str', '')).strip(),
                'speed': self._strip_ansi(d.get('_speed_str', '')).strip(),
                'eta': self._strip_ansi(d.get('_eta_str', '')).strip(),
            }
        elif d['status'] == 'finished':
            total = self._strip_ansi(d.get('_total_bytes_str', '')).strip()
            self._last_total = total
            self._progress = {
                'status': 'finished',
                'total': total,
            }

    def _postprocessor_hook(self, d):
        """yt-dlp postprocessor callback (FFmpeg 변환 등)"""
        status = d.get('status', '')
        if status == 'started':
            self._progress = {
                'status': 'converting',
                'percent': '',
                'total': '',
                'speed': '',
                'eta': '',
                'postprocessor': d.get('postprocessor', ''),
            }
        elif status == 'finished':
            self._progress = {
                'status': 'converting_done',
                'total': self._last_total,
            }

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information about a YouTube video

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with video information or None
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            **self.ydl_opts_base,
            'format': 'best',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    logger.warning(f"No info extracted for {video_id}")
                    return None

                # Extract relevant fields
                video_info = {
                    'id': video_id,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'formats': self._extract_formats(info),
                }

                logger.info(f"Got info for: {video_info['title']}")
                return video_info

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting video info for {video_id}: {e}")
            return None

    def _extract_formats(self, info: Dict) -> List[Dict]:
        """
        Extract available formats from video info

        Args:
            info: Video info dictionary from yt-dlp

        Returns:
            List of format dictionaries
        """
        formats = []

        for fmt in info.get('formats', []):
            # Skip formats without URL
            if not fmt.get('url'):
                continue

            format_info = {
                'format_id': fmt.get('format_id'),
                'ext': fmt.get('ext'),
                'quality': fmt.get('format_note', 'unknown'),
                'filesize': fmt.get('filesize', 0),
                'url': fmt.get('url'),
                'vcodec': fmt.get('vcodec', 'none'),
                'acodec': fmt.get('acodec', 'none'),
                'width': fmt.get('width'),
                'height': fmt.get('height'),
                'fps': fmt.get('fps'),
            }

            formats.append(format_info)

        return formats

    def get_best_format_url(self, video_id: str, quality: str = '720p') -> Optional[str]:
        """
        Get direct download URL for best format

        Args:
            video_id: YouTube video ID
            quality: Preferred quality (e.g., '720p', '1080p', 'best')

        Returns:
            Direct download URL or None
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Format selection based on quality
        if quality == 'best':
            format_string = 'best[vcodec^=avc1][ext=mp4]/best[ext=mp4]/best'
        elif quality == 'audio':
            format_string = 'bestaudio[ext=m4a]/bestaudio'
        else:
            # Try to get specific quality
            height = quality.replace('p', '')
            format_string = (
                f'bestvideo[height<={height}][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/'
                f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/'
                f'best[height<={height}]'
            )

        ydl_opts = {
            **self.ydl_opts_base,
            'format': format_string,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    return None

                # Get the best matching format URL
                download_url = info.get('url')

                if download_url:
                    logger.info(f"Got download URL for {video_id} ({quality})")
                    return download_url
                else:
                    logger.warning(f"No download URL found for {video_id}")
                    return None

        except Exception as e:
            logger.error(f"Error getting download URL for {video_id}: {e}")
            return None

    def get_channel_videos(self, channel_url: str, max_videos: int = 500) -> List[Dict]:
        """
        Get video list from a channel URL using yt-dlp (fallback when no API key).

        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to fetch

        Returns:
            List of video dictionaries with 'id' and 'title'
        """
        # Ensure URL points to the channel's videos tab
        url = channel_url.rstrip('/')
        
        # Remove other channel tabs if present
        for tab in ['/featured', '/playlists', '/shorts', '/streams', '/community']:
            if url.endswith(tab):
                url = url[:-len(tab)]
                break
                
        if not url.endswith('/videos'):
            url += '/videos'

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'playlistend': max_videos,
            'extractor_args': {'youtube': {'lang': ['ko']}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    logger.warning(f"No info extracted for channel: {channel_url}")
                    return [], {}

                entries = info.get('entries', [])
                videos = []
                for entry in entries:
                    if entry and entry.get('id'):
                        videos.append({
                            'id': entry['id'],
                            'title': entry.get('title', 'Unknown'),
                            'availability': entry.get('availability'),
                        })

                metadata = {
                    'channel': info.get('channel', '') or info.get('uploader', ''),
                }

                logger.info(f"yt-dlp: Retrieved {len(videos)} videos from channel (channel: {metadata['channel']})")
                return videos, metadata

        except Exception as e:
            logger.error(f"Error getting channel videos via yt-dlp: {e}")
            return [], {}

    def get_playlist_videos(self, playlist_url: str, max_videos: int = 500) -> List[Dict]:
        """
        Get video list from a playlist URL using yt-dlp (fallback when no API key).

        Args:
            playlist_url: YouTube playlist URL
            max_videos: Maximum number of videos to fetch

        Returns:
            List of video dictionaries with 'id' and 'title'
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'playlistend': max_videos,
            'extractor_args': {'youtube': {'lang': ['ko']}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)

                if not info:
                    logger.warning(f"No info extracted for playlist: {playlist_url}")
                    return [], {}

                entries = info.get('entries', [])
                videos = []
                for entry in entries:
                    if entry and entry.get('id'):
                        videos.append({
                            'id': entry['id'],
                            'title': entry.get('title', 'Unknown'),
                        })

                metadata = {
                    'playlist_title': info.get('title', ''),
                    'channel': info.get('channel', '') or info.get('uploader', ''),
                }

                logger.info(f"yt-dlp: Retrieved {len(videos)} videos from playlist (channel: {metadata['channel']}, playlist: {metadata['playlist_title']})")
                return videos, metadata

        except Exception as e:
            logger.error(f"Error getting playlist videos via yt-dlp: {e}")
            return [], {}

    def download_video(self, video_id: str, quality: str = '720p', output_dir: str = None) -> Optional[str]:
        """
        Download a video using yt-dlp (server-side download).

        Args:
            video_id: YouTube video ID
            quality: Preferred quality (e.g., '720p', '1080p', 'best', 'audio')
            output_dir: Output directory path

        Returns:
            Downloaded file path or None
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        self.reset_cancel()

        if not output_dir:
            output_dir = str(Config.DOWNLOADS_DIR)

        os.makedirs(output_dir, exist_ok=True)

        # 이전 강제 종료로 남은 임시 파일 정리
        self._cleanup_partial_files(output_dir, video_id)

        # 파일명: YYMMDD_영상제목.확장자 (영상 업로드 날짜)
        outtmpl = os.path.join(output_dir, '%(upload_date>%y%m%d)s_%(title)s.%(ext)s')

        if quality == 'audio':
            format_string = 'bestaudio/best'
            ydl_opts = {
                **self.ydl_opts_base,
                'format': format_string,
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],
                'postprocessor_hooks': [self._postprocessor_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            height = quality.replace('p', '') if quality != 'best' else ''
            if height:
                format_string = (
                    f'bestvideo[height<={height}][vcodec^=avc1]+bestaudio/'
                    f'bestvideo[height<={height}]+bestaudio/'
                    f'best[height<={height}]/best'
                )
            else:
                format_string = 'bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best'

            ydl_opts = {
                **self.ydl_opts_base,
                'format': format_string,
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],
                'merge_output_format': 'mp4',
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None

                filepath = ydl.prepare_filename(info)
                # 오디오: mp3 변환 후 확장자 변경
                if quality == 'audio':
                    base, _ = os.path.splitext(filepath)
                    filepath = base + '.mp3'
                else:
                    # 병합 시 확장자가 바뀔 수 있으므로 mp4로 변경
                    base, _ = os.path.splitext(filepath)
                    filepath = base + '.mp4'

                if os.path.exists(filepath):
                    logger.info(f"Downloaded: {filepath}")
                    return filepath
                else:
                    logger.warning(f"File not found after download: {filepath}")
                    return None

        except Exception as e:
            # 취소 요청에 의한 중단
            if self._cancel_event.is_set():
                logger.info(f"Download cancelled by user: {video_id}")
                self._cleanup_partial_files(output_dir, video_id)
                return "CANCELLED"

            error_msg = str(e).lower()
            membership_keywords = [
                'join this channel', 'members-only', 'members only',
                'membership', '멤버십', 'this video is available to this channel',
                '회원 전용', '채널에 가입',
            ]
            if any(kw in error_msg for kw in membership_keywords):
                logger.info(f"Membership-only video skipped: {video_id}")
                return "MEMBERSHIP_SKIP"
            logger.error(f"Error downloading {video_id}: {e}")
            return None

    @staticmethod
    def _cleanup_partial_files(output_dir: str, video_id: str):
        """취소 시 남은 .part / .ytdl 임시 파일 삭제"""
        for pattern in ('*.part', '*.ytdl', '*.part-Frag*'):
            for f in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    os.remove(f)
                    logger.info(f"Removed partial file: {f}")
                except OSError:
                    pass

    def get_download_info(self, video_id: str) -> Optional[Dict]:
        """
        Get complete download information with multiple quality options

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with download info for different qualities
        """
        qualities = ['360p', '720p', '1080p', 'audio']
        download_info = {
            'video_id': video_id,
            'formats': {}
        }

        # Get basic info first
        video_info = self.get_video_info(video_id)

        if not video_info:
            return None

        download_info['title'] = video_info['title']
        download_info['duration'] = video_info['duration']
        download_info['thumbnail'] = video_info['thumbnail']

        # Get URLs for each quality
        for quality in qualities:
            url = self.get_best_format_url(video_id, quality)
            if url:
                download_info['formats'][quality] = url

        return download_info


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    downloader = YouTubeDownloader()

    # Test with a video ID (replace with actual ID)
    # test_id = "dQw4w9WgXcQ"
    # info = downloader.get_download_info(test_id)
    # if info:
    #     print(f"Title: {info['title']}")
    #     print(f"Available formats: {list(info['formats'].keys())}")
