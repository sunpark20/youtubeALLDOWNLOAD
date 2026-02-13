"""
yt-dlp Auto-Updater Service

This module handles automatic updates of yt-dlp on application startup.
"""

import subprocess
import sys
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class YtdlpUpdater:
    """Manages yt-dlp updates"""

    def __init__(self):
        self.current_version: Optional[str] = None
        self.latest_version: Optional[str] = None

    def get_current_version(self) -> Optional[str]:
        """
        Get currently installed yt-dlp version

        Returns:
            str: Version string (e.g., "2025.01.15") or None if not installed
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'yt_dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                self.current_version = version
                logger.info(f"Current yt-dlp version: {version}")
                return version
            else:
                logger.warning("yt-dlp not found or error getting version")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Timeout getting yt-dlp version")
            return None
        except Exception as e:
            logger.error(f"Error getting yt-dlp version: {e}")
            return None

    def update(self) -> Tuple[bool, str]:
        """
        Update yt-dlp to the latest version

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            logger.info("Starting yt-dlp update...")

            # Use pip to update yt-dlp
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Get new version
                new_version = self.get_current_version()

                if new_version:
                    self.latest_version = new_version
                    message = f"✅ yt-dlp updated successfully to {new_version}"
                    logger.info(message)
                    return True, message
                else:
                    message = "⚠️ Update completed but couldn't verify new version"
                    logger.warning(message)
                    return True, message
            else:
                error_msg = result.stderr.strip()
                message = f"❌ Update failed: {error_msg}"
                logger.error(message)
                return False, message

        except subprocess.TimeoutExpired:
            message = "❌ Update timed out (>60s)"
            logger.error(message)
            return False, message
        except Exception as e:
            message = f"❌ Update error: {str(e)}"
            logger.error(message)
            return False, message

    def check_and_update(self) -> Tuple[bool, str]:
        """
        Check current version and update if needed

        Returns:
            Tuple[bool, str]: (success, message)
        """
        logger.info("=" * 50)
        logger.info("yt-dlp Auto-Update Check")
        logger.info("=" * 50)

        # Get current version
        current = self.get_current_version()

        if not current:
            logger.warning("yt-dlp not installed, installing...")
            return self.update()

        # Always update to ensure latest version
        logger.info(f"Current version: {current}")
        logger.info("Checking for updates...")

        return self.update()


# Global instance
updater = YtdlpUpdater()


def update_ytdlp_on_startup() -> Tuple[bool, str]:
    """
    Convenience function to update yt-dlp on application startup

    Returns:
        Tuple[bool, str]: (success, message)
    """
    return updater.check_and_update()


if __name__ == "__main__":
    # Test the updater
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Testing yt-dlp updater...")
    success, message = update_ytdlp_on_startup()
    print(f"\nResult: {message}")
    print(f"Success: {success}")
