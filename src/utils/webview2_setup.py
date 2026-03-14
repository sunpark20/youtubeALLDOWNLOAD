"""
WebView2 Runtime auto-installer for Windows.

pywebview 5.0+ requires WebView2 Runtime. On Windows 10 machines where it
is not pre-installed, webview.start() silently crashes. This module detects
the runtime and installs it automatically before the app window is created.
"""

import logging
import os
import sys
import tempfile
import urllib.request

logger = logging.getLogger("WebView2Setup")

# Microsoft's WebView2 Evergreen Bootstrapper (~1.8 MB)
_BOOTSTRAPPER_URL = (
    "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
)
_MANUAL_INSTALL_URL = (
    "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
)
# WebView2 client GUID used in EdgeUpdate registry keys
_WV2_CLIENT_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


def _timeout_hook(timeout_sec: int):
    """Return a urlretrieve reporthook that raises if no progress for *timeout_sec*."""
    import time
    state = {"last": time.monotonic()}

    def hook(block_num, block_size, total_size):
        now = time.monotonic()
        if block_num == 0:
            state["last"] = now
            return
        state["last"] = now
        if total_size > 0 and block_num * block_size >= total_size:
            return
        # Called periodically — if we ever stall, the next call will be late
        # but Python's socket-level timeout (default) handles true hangs.

    # Also set a global socket timeout so urlretrieve doesn't hang forever
    import socket
    socket.setdefaulttimeout(timeout_sec)
    return hook


def _msgbox(text: str, title: str = "YouTube ALL Downloader", style: int = 0) -> int:
    """Show a native Windows MessageBox (no tkinter dependency)."""
    import ctypes
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


def is_webview2_installed() -> bool:
    """Check whether WebView2 Runtime is installed via registry."""
    import winreg

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{_WV2_CLIENT_GUID}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{_WV2_CLIENT_GUID}"),
        (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{_WV2_CLIENT_GUID}"),
    ]

    for hive, subkey in reg_paths:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                pv, _ = winreg.QueryValueEx(key, "pv")
                if pv and pv != "0.0.0.0":
                    return True
        except OSError:
            continue

    return False


def ensure_webview2() -> None:
    """Ensure WebView2 Runtime is available; install if missing.

    - Non-Windows platforms: no-op.
    - Already installed: returns immediately (~1 ms).
    - Missing: prompts user, downloads bootstrapper, runs silent install.
    - On failure: shows manual-install URL and exits.
    """
    if sys.platform != "win32":
        return

    # Registry check — fail-open so a broken registry doesn't block the app
    try:
        if is_webview2_installed():
            logger.info("WebView2 Runtime is already installed.")
            return
    except Exception as e:
        logger.warning(f"WebView2 registry check failed ({e}); continuing anyway.")
        return

    logger.info("WebView2 Runtime not found. Starting installation...")

    # --- Ask user ---
    MB_OKCANCEL = 0x01
    MB_ICONINFORMATION = 0x40
    IDOK = 1
    result = _msgbox(
        "A required component (WebView2 Runtime) is missing.\n"
        "Click OK to install it automatically (requires internet).",
        style=MB_OKCANCEL | MB_ICONINFORMATION,
    )
    if result != IDOK:
        logger.info("User cancelled WebView2 installation.")
        sys.exit(0)

    # --- Download bootstrapper ---
    try:
        tmp = tempfile.mkdtemp()
        installer_path = os.path.join(tmp, "MicrosoftEdgeWebview2Setup.exe")
        logger.info(f"Downloading WebView2 bootstrapper to {installer_path}...")
        urllib.request.urlretrieve(_BOOTSTRAPPER_URL, installer_path, _timeout_hook(30))
    except Exception as e:
        logger.error(f"WebView2 bootstrapper download failed: {e}")
        _msgbox(
            f"Failed to download the installer.\n\n"
            f"Please install WebView2 Runtime manually:\n{_MANUAL_INSTALL_URL}",
        )
        sys.exit(1)

    # --- Run installer with UAC elevation ---
    try:
        import ctypes
        logger.info("Running WebView2 installer (requesting elevation)...")
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", installer_path, "/silent /install", None, 0
        )
        # ShellExecuteW returns > 32 on success
        if ret <= 32:
            raise RuntimeError(f"ShellExecuteW returned {ret}")
        # Wait for installer to finish (poll registry, max ~120s)
        import time
        for i in range(60):
            time.sleep(2)
            if is_webview2_installed():
                logger.info("WebView2 Runtime installed successfully.")
                return
        raise RuntimeError("Installation timed out (registry key not found after 120s)")
    except Exception as e:
        logger.error(f"WebView2 installation failed: {e}")
        _msgbox(
            f"Installation failed.\n\n"
            f"Please install WebView2 Runtime manually:\n{_MANUAL_INSTALL_URL}",
        )
        sys.exit(1)
