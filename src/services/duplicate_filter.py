"""
Duplicate Filter Service

Handles deduplication of videos at two levels:
1. API-level: Remove duplicate video IDs using Set
2. File-level: Check if file already exists locally using SHA-256
"""

import logging
import hashlib
import os
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class DuplicateFilter:
    """Manages video deduplication"""

    def __init__(self):
        self.seen_video_ids: Set[str] = set()
        self.local_file_hashes: Dict[str, str] = {}

    def deduplicate_video_ids(self, videos: List[Dict]) -> List[Dict]:
        """
        Remove duplicate videos based on video ID

        Uses Set for O(1) lookup time

        Args:
            videos: List of video dictionaries with 'id' field

        Returns:
            Deduplicated list of videos
        """
        unique_videos = []
        video_ids_seen = set()

        for video in videos:
            video_id = video.get('id')

            if not video_id:
                logger.warning(f"Video without ID found: {video}")
                continue

            if video_id not in video_ids_seen:
                unique_videos.append(video)
                video_ids_seen.add(video_id)
            else:
                logger.debug(f"Duplicate video ID filtered: {video_id}")

        removed_count = len(videos) - len(unique_videos)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate video(s)")
            logger.info(f"Unique videos: {len(unique_videos)}")

        return unique_videos

    @staticmethod
    def calculate_file_hash(filepath: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA-256 hash of a file

        Args:
            filepath: Path to file
            chunk_size: Size of chunks to read (default: 8KB)

        Returns:
            SHA-256 hash as hex string
        """
        sha256 = hashlib.sha256()

        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)

            return sha256.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating hash for {filepath}: {e}")
            return ""

    def scan_local_files(self, directory: str) -> Dict[str, str]:
        """
        Scan local directory and build hash database

        Args:
            directory: Directory to scan

        Returns:
            Dictionary mapping filename to hash
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return {}

        file_hashes = {}

        try:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    # Only scan video/audio files
                    if any(filename.endswith(ext) for ext in [
                        '.mp4', '.webm', '.mkv', '.avi', '.mov',
                        '.mp3', '.m4a', '.opus', '.ogg', '.wav'
                    ]):
                        filepath = os.path.join(root, filename)
                        file_hash = self.calculate_file_hash(filepath)

                        if file_hash:
                            file_hashes[filename] = file_hash
                            logger.debug(f"Scanned: {filename} -> {file_hash[:16]}...")

            logger.info(f"Scanned {len(file_hashes)} local files in {directory}")
            self.local_file_hashes = file_hashes

            return file_hashes

        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            return file_hashes

    def is_file_downloaded(self, video_id: str, directory: str) -> bool:
        """
        Check if video is already downloaded

        Simple filename-based check (faster than hash)

        Args:
            video_id: YouTube video ID
            directory: Download directory

        Returns:
            True if file exists with video_id in filename
        """
        if not os.path.exists(directory):
            return False

        try:
            for filename in os.listdir(directory):
                # Check if video_id is in filename
                # YouTube video files usually contain the ID
                if video_id in filename:
                    logger.debug(f"Video {video_id} already exists: {filename}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking local files: {e}")
            return False

    def filter_already_downloaded(
        self,
        videos: List[Dict],
        download_directory: str
    ) -> List[Dict]:
        """
        Filter out videos that are already downloaded

        Args:
            videos: List of video dictionaries
            download_directory: Directory to check

        Returns:
            List of videos not yet downloaded
        """
        if not os.path.exists(download_directory):
            logger.info("Download directory doesn't exist, no files to skip")
            return videos

        new_videos = []
        skipped = 0

        for video in videos:
            video_id = video.get('id')

            if not video_id:
                continue

            if not self.is_file_downloaded(video_id, download_directory):
                new_videos.append(video)
            else:
                skipped += 1
                logger.info(f"Skipping already downloaded: {video.get('title', video_id)}")

        logger.info(f"Filtered {skipped} already downloaded video(s)")
        logger.info(f"New videos to download: {len(new_videos)}")

        return new_videos

    def get_deduplication_stats(self) -> Dict:
        """
        Get statistics about deduplication

        Returns:
            Dictionary with stats
        """
        return {
            'seen_video_ids': len(self.seen_video_ids),
            'local_files_scanned': len(self.local_file_hashes)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test deduplication
    filter_service = DuplicateFilter()

    # Test data with duplicates
    test_videos = [
        {'id': 'video1', 'title': 'Video 1'},
        {'id': 'video2', 'title': 'Video 2'},
        {'id': 'video1', 'title': 'Video 1 (duplicate)'},
        {'id': 'video3', 'title': 'Video 3'},
        {'id': 'video2', 'title': 'Video 2 (duplicate)'},
    ]

    print("Original videos:", len(test_videos))
    unique = filter_service.deduplicate_video_ids(test_videos)
    print("After deduplication:", len(unique))
    print("Unique videos:", [v['title'] for v in unique])
