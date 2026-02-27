"""
YouTube Downloader Service

Wrapper around yt-dlp for extracting download information
"""

import logging
import os
import yt_dlp
from typing import Dict, List, Optional

from utils.config import Config

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """yt-dlp wrapper for YouTube downloads"""

    def __init__(self):
        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {'youtube': {'lang': ['ko']}},
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
            format_string = 'best[ext=mp4]/best'
        elif quality == 'audio':
            format_string = 'bestaudio[ext=m4a]/bestaudio'
        else:
            # Try to get specific quality
            height = quality.replace('p', '')
            format_string = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]'

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
        if '/videos' not in url:
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

        if not output_dir:
            output_dir = str(Config.DOWNLOADS_DIR)

        os.makedirs(output_dir, exist_ok=True)

        if quality == 'audio':
            format_string = 'bestaudio[ext=m4a]/bestaudio'
        else:
            height = quality.replace('p', '') if quality != 'best' else ''
            if height:
                format_string = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
            else:
                format_string = 'best[ext=mp4]/best'

        ydl_opts = {
            **self.ydl_opts_base,
            'format': format_string,
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        }

        if quality != 'audio':
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None

                filepath = ydl.prepare_filename(info)
                # 병합 시 확장자가 바뀔 수 있으므로 mp4로 변경
                if quality != 'audio':
                    base, _ = os.path.splitext(filepath)
                    filepath = base + '.mp4'

                if os.path.exists(filepath):
                    logger.info(f"Downloaded: {filepath}")
                    return filepath
                else:
                    logger.warning(f"File not found after download: {filepath}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading {video_id}: {e}")
            return None

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
