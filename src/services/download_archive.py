"""
Download Archive Service

Manages a per-folder download_archive.txt that records which video IDs
have been downloaded. Uses the same format as yt-dlp's --download-archive.
"""

import os
import re
import logging
from typing import Set

logger = logging.getLogger(__name__)


class DownloadArchive:
    """Manages download archive for tracking downloaded videos"""

    ARCHIVE_FILENAME = ".download_archive"

    def __init__(self, directory: str):
        self.directory = directory
        self.archive_path = os.path.join(directory, self.ARCHIVE_FILENAME)
        self._cached_ids: Set[str] = set()
        self._loaded = False

    def _load(self):
        """Load archive from file into memory (lazy loading)"""
        if self._loaded:
            return

        self._cached_ids = set()

        if os.path.exists(self.archive_path):
            try:
                with open(self.archive_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Format: "youtube VIDEO_ID"
                            parts = line.split()
                            if len(parts) >= 2:
                                self._cached_ids.add(parts[1])
                            elif len(parts) == 1:
                                self._cached_ids.add(parts[0])

                logger.info(f"Loaded {len(self._cached_ids)} entries from archive: {self.archive_path}")
            except Exception as e:
                logger.error(f"Error loading archive {self.archive_path}: {e}")

        self._loaded = True

    def has_video(self, video_id: str) -> bool:
        """Check if video ID is in the archive"""
        self._load()
        return video_id in self._cached_ids

    def add_video(self, video_id: str):
        """Add a video ID to the archive after successful download"""
        self._load()

        if video_id in self._cached_ids:
            return

        os.makedirs(self.directory, exist_ok=True)

        try:
            with open(self.archive_path, 'a', encoding='utf-8') as f:
                f.write(f"youtube {video_id}\n")
            self._cached_ids.add(video_id)
            logger.debug(f"Added to archive: {video_id}")
        except Exception as e:
            logger.error(f"Error writing to archive: {e}")

    def remove_video(self, video_id: str):
        """Remove a video ID from the archive (file was deleted)"""
        self._load()

        if video_id not in self._cached_ids:
            return

        self._cached_ids.discard(video_id)

        # Rewrite archive file without the removed ID
        try:
            if os.path.exists(self.archive_path):
                with open(self.archive_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                with open(self.archive_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        parts = line.strip().split()
                        vid = parts[1] if len(parts) >= 2 else parts[0] if parts else ''
                        if vid != video_id:
                            f.write(line)
                logger.info(f"Removed from archive: {video_id}")
        except Exception as e:
            logger.error(f"Error removing from archive: {e}")

    def count(self) -> int:
        """Return number of archived videos"""
        self._load()
        return len(self._cached_ids)

    def import_existing_files(self):
        """
        Scan existing files in directory and import their video IDs into the archive.
        Handles two filename patterns:
          - New format: "Title [VIDEO_ID].ext"
          - Legacy format: files without ID (try to match via yt-dlp metadata)
        """
        if not os.path.exists(self.directory):
            return 0

        self._load()
        imported = 0
        video_extensions = {'.mp4', '.webm', '.mkv', '.avi', '.mov',
                            '.mp3', '.m4a', '.opus', '.ogg', '.wav'}

        # Pattern to extract [VIDEO_ID] from filename
        id_pattern = re.compile(r'\[([a-zA-Z0-9_-]{11})\]\.[a-zA-Z0-9]+$')

        for filename in os.listdir(self.directory):
            if filename == self.ARCHIVE_FILENAME:
                continue

            _, ext = os.path.splitext(filename)
            if ext.lower() not in video_extensions:
                continue

            # Try to extract video ID from filename
            match = id_pattern.search(filename)
            if match:
                vid = match.group(1)
                if vid not in self._cached_ids:
                    self.add_video(vid)
                    imported += 1

        if imported > 0:
            logger.info(f"Imported {imported} existing files into archive")

        return imported


def get_archive(directory: str) -> DownloadArchive:
    """Factory function to get an archive instance for a directory"""
    return DownloadArchive(directory)
