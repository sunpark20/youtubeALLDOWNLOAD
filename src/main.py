"""
YouTube ALL DOWNLOADER - Main Application Entry Point

Desktop application using pywebview + FastAPI
"""

import sys
from pathlib import Path
import threading
import time
import logging
import traceback
import urllib.request
import webview

from utils.logger import setup_logger
from utils.config import Config
from utils.crash_reporter import send_crash_report
from services.updater import update_ytdlp_on_startup

# Setup logging
logger = setup_logger("Main", logging.INFO)


def _check_single_instance():
    """이미 실행 중인 인스턴스가 있으면 종료"""
    import socket

    # 1) 포트 체크 (크로스 플랫폼) — 이미 서버가 떠 있는지 확인
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((Config.HOST, Config.PORT))
        sock.close()
        if result == 0:  # 포트가 이미 열려 있음 = 다른 인스턴스 실행 중
            logger.warning("Another instance is already running (port in use). Exiting.")
            sys.exit(0)
    except Exception:
        pass

    # 2) Windows Named Mutex — 더 확실한 방지
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\YouTubeBulkDownloaderMutex"
        mutex = kernel32.CreateMutexW(None, True, mutex_name)
        last_error = ctypes.get_last_error()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            logger.warning("Another instance is already running (mutex). Exiting.")
            kernel32.CloseHandle(mutex)
            sys.exit(0)
        # mutex를 반환하지 않고 프로세스 수명 동안 유지 (GC 방지)
        _check_single_instance._mutex = mutex


def _handle_uncaught_exception(exc_type, exc_value, exc_tb):
    """Log any uncaught exception before the process dies."""
    logger.critical(
        "Uncaught exception:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )
    send_crash_report(exc_type, exc_value, exc_tb)


sys.excepthook = _handle_uncaught_exception


def _check_environment():
    """
    Validate runtime environment and log diagnostics.
    Catches the two most common Intel Mac launch failures:
      1. PyObjC version mismatch (webview backend cannot initialise)
      2. ffmpeg binary missing from the bundle / PATH
    """
    import platform
    import shutil

    logger.info(f"Python {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.machine()}")

    # --- 1. PyObjC check (macOS only) ---
    if sys.platform == "darwin":
        try:
            import objc
            logger.info(f"PyObjC version: {objc.__version__}")
        except ImportError as e:
            logger.critical(f"PyObjC import failed — webview cannot start on macOS: {e}")
            logger.critical("Fix: rebuild with 'pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-WebKit'")

        try:
            import WebKit  # noqa: F401
            logger.info("WebKit framework: OK")
        except ImportError as e:
            logger.critical(f"WebKit import failed: {e}")

    # --- 2. ffmpeg check ---
    if getattr(sys, "frozen", False):
        # Packaged app: ffmpeg should be next to the executable
        exe_dir = Path(sys.executable).parent
        ffmpeg_bin = exe_dir / "ffmpeg"
        if ffmpeg_bin.exists():
            logger.info(f"ffmpeg (bundled): {ffmpeg_bin}")
        else:
            logger.warning(f"ffmpeg NOT found in bundle at {ffmpeg_bin}")
            # Fall back to PATH
            fallback = shutil.which("ffmpeg")
            if fallback:
                logger.info(f"ffmpeg (PATH fallback): {fallback}")
            else:
                logger.error("ffmpeg not found — downloads requiring merge will fail")
    else:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            logger.info(f"ffmpeg: {ffmpeg_path}")
        else:
            logger.warning("ffmpeg not found in PATH (development mode)")


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

    _check_single_instance()

    # Step 0: Validate environment (PyObjC, ffmpeg, arch)
    _check_environment()

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
        # Report startup failure so we know the server never came up
        send_crash_report(
            RuntimeError,
            RuntimeError("Server failed to start within 10 seconds"),
            None,
        )

    # Step 3: Create pywebview window
    logger.info("Creating desktop window...")

    # Application URL
    app_url = f"http://{Config.HOST}:{Config.PORT}"

    # Create window
    window = webview.create_window(
        title=Config.APP_NAME,
        url=app_url,
        width=1300,
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
        import os
        os._exit(0)


if __name__ == "__main__":
    # Add freeze_support to prevent fork bombs (infinite window spawning)
    # when pyinstaller packaged app uses multiprocessing on macOS/Windows
    import multiprocessing
    multiprocessing.freeze_support()

    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        send_crash_report(*sys.exc_info())
        sys.exit(1)
