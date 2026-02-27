"""
YouTube ALL DOWNLOADER - Main Application Entry Point

Desktop application using pywebview + FastAPI
"""

import sys
import threading
import time
import logging
import urllib.request
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

    # Run uvicorn server properly in a thread
    import asyncio
    
    # Create config
    config = uvicorn.Config(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="error",
        access_log=False,
    )
    
    server = uvicorn.Server(config)
    
    # Disable signal handlers as we're not in the main thread
    server.install_signal_handlers = lambda: None
    
    server.run()


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

    # Wait for server to be ready (health check polling)
    health_url = f"http://{Config.HOST}:{Config.PORT}/api/health"
    server_ready = False
    for _ in range(20):  # max 10 seconds (20 * 0.5s)
        try:
            urllib.request.urlopen(health_url, timeout=1)
            server_ready = True
            break
        except Exception:
            time.sleep(0.5)

    if not server_ready:
        logger.warning("Server did not respond to health check within 10s, proceeding anyway")

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
            debug=False,
            http_server=False,
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
