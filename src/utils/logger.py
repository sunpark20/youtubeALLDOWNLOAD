"""
Logging Configuration

Centralized logging setup for the application
"""

import logging
import sys
import platform
from pathlib import Path
from datetime import datetime


def _get_log_dir() -> Path:
    """Return platform-appropriate log directory."""
    if platform.system() == "Darwin":
        log_dir = Path.home() / "Library" / "Logs" / "YT-Chita"
    elif platform.system() == "Windows":
        import os
        appdata = os.environ.get("APPDATA", "")
        if not appdata or not Path(appdata).exists():
            appdata = str(Path.home())
        log_dir = Path(appdata) / "YT-Chita" / "Logs"
    else:
        log_dir = Path.home() / ".local" / "share" / "YT-Chita" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _setup_root_logger(level: int = logging.INFO):
    """
    루트 로거에 핸들러를 설정하여 모든 모듈의 로그를 캡처.
    logging.getLogger(__name__) 으로 생성된 로거도 자동으로 파일에 기록됨.
    """
    root = logging.getLogger()

    # 이미 설정되어 있으면 스킵
    if root.handlers:
        return

    root.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # File handler
    try:
        log_dir = _get_log_dir()
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        print(f"[Logger] Log file: {log_file}", file=sys.stderr)
    except Exception as e:
        print(f"[Logger] Could not create file handler: {e}", file=sys.stderr)


def setup_logger(name: str = "YTBulkDownloader", level: int = logging.INFO) -> logging.Logger:
    """
    Setup and configure application logger

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    _setup_root_logger(level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


# Global logger instance
logger = setup_logger()


if __name__ == "__main__":
    # Test logger
    test_logger = setup_logger("TestLogger", logging.DEBUG)
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
