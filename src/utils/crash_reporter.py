"""
Crash Reporter

Collects crash info (traceback, system info, recent logs) and sends it
to a Google Apps Script webhook via HTTP POST.
Uses only stdlib — no extra dependencies.
"""

import json
import logging
import platform
import sys
import threading
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("CrashReporter")

# Google Apps Script web app URL (deploy as web app → "Anyone" access)
# Replace with your actual deployed URL.
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxiDJf0xQN6YbTrLrEIdjH-ZUbIlvsIhDevj2cOXby0scOFYuStgLrQZuwvUIgF5UOh/exec"

# Deduplication: track already-reported error signatures within this session
_reported_signatures: set[str] = set()


def send_crash_report(exc_type, exc_value, exc_tb):
    """Collect crash info and send it asynchronously to the webhook."""
    if not WEBHOOK_URL:
        logger.debug("Crash reporter webhook URL not configured, skipping.")
        return

    # Deduplicate: same (type, message) only reported once per session
    sig = f"{exc_type.__name__}:{exc_value}"
    if sig in _reported_signatures:
        logger.debug("Crash already reported this session, skipping.")
        return
    _reported_signatures.add(sig)

    try:
        data = _collect_report(exc_type, exc_value, exc_tb)
    except Exception:
        logger.debug("Failed to collect crash report", exc_info=True)
        return

    # Fire-and-forget in a daemon thread so the app can exit promptly
    t = threading.Thread(target=_post_report, args=(data,), daemon=True)
    t.start()
    # Give it a moment, but don't block shutdown for too long
    t.join(timeout=5)


def _collect_report(exc_type, exc_value, exc_tb) -> dict:
    """Gather system info, traceback, and recent log lines."""
    from utils.config import Config

    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    return {
        "app_version": Config.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "frozen": getattr(sys, "frozen", False),
        "error_type": exc_type.__name__,
        "error_message": str(exc_value),
        "traceback": tb_text,
        "recent_log": _read_recent_log(50),
    }


def _read_recent_log(lines: int = 50) -> str:
    """Read the last *lines* from today's log file."""
    try:
        if platform.system() == "Darwin":
            log_dir = Path.home() / "Library" / "Logs" / "YT-Chita"
        elif platform.system() == "Windows":
            import os as _os
            log_dir = Path(_os.environ.get("APPDATA", Path.home())) / "YT-Chita" / "Logs"
        else:
            log_dir = Path.home() / ".local" / "share" / "YT-Chita" / "logs"

        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        if not log_file.exists():
            return "(log file not found)"

        all_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(all_lines[-lines:])
    except Exception as e:
        return f"(failed to read log: {e})"


def _post_report(data: dict):
    """HTTP POST JSON payload to the Google Apps Script webhook."""
    try:
        payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.debug("Crash report sent, status %s", resp.status)
    except Exception:
        # Best-effort — never let the reporter itself crash the app
        logger.debug("Failed to send crash report", exc_info=True)
