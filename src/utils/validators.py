"""
Input Validators

Validate user inputs and URLs
"""

import re
from typing import Optional, Tuple


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if URL is a valid YouTube URL

    Args:
        url: URL string to validate

    Returns:
        True if valid YouTube URL
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/channel/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/@[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/c/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/user/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(https?://)?youtu\.be/[\w-]+',
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True

    return False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL

    Args:
        url: YouTube video URL

    Returns:
        Video ID or None
    """
    patterns = [
        r'watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'embed/([\w-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Check if it's already a video ID
    if re.match(r'^[\w-]{11}$', url):
        return url

    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """
    Extract playlist ID from YouTube URL

    Args:
        url: YouTube playlist URL

    Returns:
        Playlist ID or None
    """
    pattern = r'list=([\w-]+)'
    match = re.search(pattern, url)

    if match:
        return match.group(1)

    # Check if it's already a playlist ID
    if url.startswith('PL') or url.startswith('UU'):
        return url

    return None


def validate_quality(quality: str) -> Tuple[bool, str]:
    """
    Validate video quality selection

    Args:
        quality: Quality string (e.g., '720p', 'audio')

    Returns:
        Tuple of (is_valid, normalized_quality)
    """
    valid_qualities = ['360p', '720p', '1080p', 'audio', 'best']

    quality = quality.lower().strip()

    if quality in valid_qualities:
        return True, quality

    return False, '720p'  # Default fallback


if __name__ == "__main__":
    # Test validators
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/@channelname",
        "https://www.youtube.com/channel/UC123456789",
        "not a youtube url",
    ]

    for url in test_urls:
        valid = is_valid_youtube_url(url)
        video_id = extract_video_id(url)
        print(f"URL: {url}")
        print(f"  Valid: {valid}")
        print(f"  Video ID: {video_id}")
        print()

    # Test quality validation
    qualities = ['720p', '1080p', 'audio', 'invalid', '4k']
    for q in qualities:
        valid, normalized = validate_quality(q)
        print(f"Quality: {q} -> Valid: {valid}, Normalized: {normalized}")
