"""
YouTube ALL DOWNLOADER - Main Application Entry Point

Desktop application using pywebview + FastAPI
"""

import sys
import threading
import time
import logging
import webview

from utils.logger import setup_logger
from utils.config import Config
from services.updater import update_ytdlp_on_startup

# Setup logging
logger = setup_logger("Main", logging.INFO)


def start_fastapi_server():
    """
    Start FastAPI server in background thread
    """
    import uvicorn
    from api.server import app

    logger.info(f"Starting FastAPI server on {Config.HOST}:{Config.PORT}")

    # Run uvicorn server
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="error",  # Reduce noise in logs
        access_log=False,
    )


def main():
    """
    Main application entry point

    Flow:
    1. Update yt-dlp
    2. Start FastAPI server in background
    3. Create pywebview window
    4. Load web UI
    """
    logger.info("=" * 70)
    logger.info(f"{Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info("=" * 70)

    # Step 1: Update yt-dlp on startup
    logger.info("Checking yt-dlp updates...")
    try:
        success, message = update_ytdlp_on_startup()
        logger.info(message)

        if not success:
            logger.warning("yt-dlp update failed, but continuing...")

    except Exception as e:
        logger.error(f"yt-dlp update error: {e}")
        logger.warning("Continuing without update...")

    # Step 2: Start FastAPI server in background thread
    logger.info("Starting background server...")
    server_thread = threading.Thread(target=start_fastapi_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    # Step 3: Create pywebview window
    logger.info("Creating desktop window...")

    # Application URL
    app_url = f"http://{Config.HOST}:{Config.PORT}"

    # Create window
    window = webview.create_window(
        title=Config.APP_NAME,
        url=app_url,
        width=1200,
        height=900,
        resizable=True,
        frameless=False,
        easy_drag=False,
        background_color='#FFFFFF',
        text_select=True,
    )

    logger.info(f"Window created: {app_url}")
    logger.info("Application starting...")
    logger.info("=" * 70)

    # Step 4: Start the application (blocking call)
    try:
        webview.start(
            debug=False,  # Set to True for development
            http_server=False,  # We're using FastAPI, not built-in server
        )
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        logger.info("Application shut down")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
