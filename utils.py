import requests
import platform
import stat
import subprocess
import os
import sys
import json
import shutil
import re
import streamlit as st

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_config.json")
BIN_DIR = os.path.join(os.path.expanduser("~"), ".youtube_downloader_bin")

def load_config():
    default = {"channel_handle": "ichon_yoga", "download_path": os.path.expanduser("~"), "include_shorts": False}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return default

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def resolve_resource_path(path):
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, path)
        if os.path.exists(p): return p

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        p = os.path.join(base_dir, path)
        if os.path.exists(p): return p
        p = os.path.join(base_dir, '..', 'Resources', path)
        if os.path.exists(p): return os.path.abspath(p)

    if os.path.exists(path): return path

    return path

def get_ffmpeg_path():
    bundled_path = resolve_resource_path("ffmpeg")
    if os.path.exists(bundled_path) and os.access(bundled_path, os.X_OK):
        return os.path.abspath(bundled_path)

    return shutil.which("ffmpeg")

def get_yt_dlp_path():
    if not os.path.exists(BIN_DIR):
        os.makedirs(BIN_DIR)
    
    filename = "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp"
    return os.path.join(BIN_DIR, filename)

def download_yt_dlp():
    target_path = get_yt_dlp_path()
    system = platform.system()
    
    url = ""
    if system == "Darwin":
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
    elif system == "Windows":
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    else:
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
        
    try:
        with st.spinner(f"🚀 다운로드 엔진(yt-dlp)을 설치/업데이트 중입니다... ({url})"):
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 실행 권한 부여 (Mac/Linux)
            if system != "Windows":
                st_mode = os.stat(target_path).st_mode
                os.chmod(target_path, st_mode | stat.S_IEXEC)
                
        return True, "설치 완료"
    except Exception as e:
        return False, f"설치 실패: {str(e)}"

def update_yt_dlp_binary():
    cmd = [get_yt_dlp_path(), "-U"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except Exception as e:
        return False, str(e)

def check_system_requirements():
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        st.error("❌ FFmpeg가 없습니다. 앱 내장 파일 또는 시스템 설치가 필요합니다.")
        st.stop()
    
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]

    yt_dlp_path = get_yt_dlp_path()
    if not os.path.exists(yt_dlp_path):
        success, msg = download_yt_dlp()
        if not success:
            st.error(f"❌ 다운로드 엔진 설치 실패: {msg}")
            st.stop()
        else:
            st.rerun()

def get_yt_dlp_cmd():
    return [get_yt_dlp_path()]

def get_archive_file(folder_path, archive_name=".download_archive.txt"):
    return os.path.join(folder_path, archive_name)

def sync_archive(folder_path, archive_name=".download_archive.txt"):
    archive_file = get_archive_file(folder_path, archive_name)

    existing_ids = set()
    id_pattern = re.compile(r'\[([a-zA-Z0-9_-]{11})\]')
    partial_pattern = re.compile(r'\.f\d+\.')

    folder_path = os.path.abspath(folder_path)

    if os.path.exists(folder_path):
        for root, dirs, files in os.walk(folder_path):
            rel_path = os.path.relpath(root, folder_path)
            depth = 0 if rel_path == '.' else len(rel_path.split(os.sep))

            if depth > 2:
                dirs[:] = []
                continue

            if "all_videos_audio" in archive_name:
                if "_모든 동영상_음성" not in root:
                    continue
            elif "all_videos" in archive_name:
                if "_모든 동영상" not in root or "_모든 동영상_음성" in root:
                    continue
            elif "all_playlists_audio" in archive_name:
                if "_모든 동영상" in root or "플레이리스트" in root or "개별_" in root:
                    continue
                if "_음성" not in root:
                    continue
                if depth < 2:
                    continue
            elif "all_playlists" in archive_name:
                if "_모든 동영상" in root or "플레이리스트" in root or "개별_" in root or "_음성" in root:
                    continue
                if depth < 2:
                    continue
            elif "individual_playlist_audio" in archive_name:
                if "플레이리스트_음성" not in root:
                    continue
            elif "individual_playlist" in archive_name:
                if "플레이리스트" not in root or "플레이리스트_음성" in root:
                    continue

            for file in files:
                if file.startswith('.') or file == os.path.basename(archive_file): continue
                if file.endswith('.part'): continue
                if partial_pattern.search(file): continue
                match = id_pattern.search(file)
                if match:
                    existing_ids.add(f"youtube {match.group(1)}")

    if existing_ids:
        with open(archive_file, 'w', encoding='utf-8') as f:
            for video_id in sorted(existing_ids):
                f.write(f"{video_id}\n")
    else:
        if os.path.exists(archive_file):
            os.remove(archive_file)