"""
YouTube Data API v3 Service

Handles all interactions with YouTube Data API:
- Get channel videos
- Get playlist videos
- Extract video information
"""

import logging
import re
from typing import List, Dict, Optional, Set
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class YouTubeAPIService:
    """YouTube Data API v3 wrapper"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube API service

        Args:
            api_key: YouTube Data API key (optional, can be set later)
        """
        self.api_key = api_key
        self.youtube = None

        if api_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize YouTube API client"""
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("YouTube API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            raise

    def set_api_key(self, api_key: str):
        """
        Set API key and initialize client

        Args:
            api_key: YouTube Data API key
        """
        self.api_key = api_key
        self._initialize_client()

    @staticmethod
    def extract_channel_id(url: str) -> Optional[str]:
        """
        Extract channel ID (UC...) from YouTube URL

        Args:
            url: YouTube channel URL

        Returns:
            Channel ID or None
        """
        if not url:
            return None

        # Already a channel ID
        if url.startswith('UC') and len(url) == 24:
            return url

        # Extract from URL
        match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_username(url: str) -> Optional[str]:
        """
        Extract username or handle from YouTube URL
        
        Args:
            url: YouTube channel URL
            
        Returns:
            Username/handle or None
        """
        if not url:
            return None
            
        patterns = [
            r'youtube\.com/@([^/?&#]+)',
            r'youtube\.com/c/([^/?&#]+)',
            r'youtube\.com/user/([^/?&#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                # URL decode in case of Korean/special characters (e.g. %EC%BD%A4%EB%AF%80)
                from urllib.parse import unquote
                return unquote(match.group(1))

        return None

    def get_channel_id_from_username(self, username: str) -> Optional[str]:
        """
        Get channel ID from username/handle

        Args:
            username: YouTube username or handle (without @)

        Returns:
            Channel ID or None
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized")
            return None

        try:
            # Remove @ if present
            username = username.lstrip('@')

            # Search for channel
            request = self.youtube.search().list(
                part='snippet',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()

            if response.get('items'):
                channel_id = response['items'][0]['id']['channelId']
                logger.info(f"Found channel ID for @{username}: {channel_id}")
                return channel_id

            logger.warning(f"No channel found for username: {username}")
            return None

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting channel ID: {e}")
            return None

    def get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """
        Get the uploads playlist ID for a channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            Uploads playlist ID or None
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized")
            return None

        try:
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()

            if response.get('items'):
                uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                logger.info(f"Uploads playlist ID: {uploads_id}")
                return uploads_id

            logger.warning(f"No channel found with ID: {channel_id}")
            return None

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting uploads playlist: {e}")
            return None

    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """
        Get playlist metadata (title, channel)

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            Dict containing playlist title and channel title, or None
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized")
            return None

        try:
            request = self.youtube.playlists().list(
                part='snippet',
                id=playlist_id
            )
            response = request.execute()

            if response.get('items'):
                snippet = response['items'][0]['snippet']
                return {
                    'title': snippet.get('title', ''),
                    'channelTitle': snippet.get('channelTitle', '')
                }
            return None

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None

    def get_playlist_videos(self, playlist_id: str, max_results: int = 500) -> List[Dict]:
        """
        Get all video IDs from a playlist

        Args:
            playlist_id: YouTube playlist ID
            max_results: Maximum number of videos to fetch (default: 500)

        Returns:
            List of video dictionaries with id, title, publishedAt
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized")
            return []

        videos = []
        next_page_token = None

        try:
            while len(videos) < max_results:
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    snippet = item['snippet']
                    videos.append({
                        'id': snippet['resourceId']['videoId'],
                        'title': snippet['title'],
                        'publishedAt': snippet['publishedAt']
                    })

                next_page_token = response.get('nextPageToken')

                if not next_page_token:
                    break

            logger.info(f"Retrieved {len(videos)} videos from playlist {playlist_id}")
            return videos

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return videos
        except Exception as e:
            logger.error(f"Error getting playlist videos: {e}")
            return videos

    def get_channel_videos(self, channel_id: str, max_results: int = 500) -> List[Dict]:
        """
        Get all uploaded videos from a channel

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch

        Returns:
            List of video dictionaries
        """
        # Get uploads playlist ID
        uploads_id = self.get_uploads_playlist_id(channel_id)

        if not uploads_id:
            logger.error("Could not get uploads playlist ID")
            return []

        # Get videos from uploads playlist
        return self.get_playlist_videos(uploads_id, max_results)

    def get_channel_playlists(self, channel_id: str) -> List[Dict]:
        """
        Get all playlists from a channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            List of playlist dictionaries with id, title
        """
        if not self.youtube:
            logger.error("YouTube API client not initialized")
            return []

        playlists = []
        next_page_token = None

        try:
            while True:
                request = self.youtube.playlists().list(
                    part='snippet',
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    playlists.append({
                        'id': item['id'],
                        'title': item['snippet']['title']
                    })

                next_page_token = response.get('nextPageToken')

                if not next_page_token:
                    break

            logger.info(f"Retrieved {len(playlists)} playlists from channel {channel_id}")
            return playlists

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return playlists
        except Exception as e:
            logger.error(f"Error getting channel playlists: {e}")
            return playlists


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test (requires API key)
    # api_key = "YOUR_API_KEY"
    # service = YouTubeAPIService(api_key)
    # videos = service.get_channel_videos("UC...")
    # print(f"Found {len(videos)} videos")
