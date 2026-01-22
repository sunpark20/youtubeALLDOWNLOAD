import os
import time
import re
import subprocess
import streamlit as st
from utils import get_yt_dlp_cmd, get_archive_file, sync_archive

# app.py 호환성 유지용 상수
VIDEO_FORMAT_OPTIONS = [] 
AUDIO_FORMAT_OPTIONS = ['--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0']
STABLE_OPTIONS = []

def get_subtitle_options():
    return [
        '--write-subs',
        '--write-auto-subs',
        '--sub-langs', 'all',
        '--embed-subs'
    ]

def get_base_options(download_path):
    # -P: 다운로드 경로
    # --newline: 진행바를 새 줄로 출력 (파싱용)
    # --no-colors: 색상 코드 제거
    # --no-warnings: YouTube PO Token 관련 경고 메시지 숨김 (다운로드는 정상 작동)
    # --progress-template: 파싱하기 쉬운 포맷 지정
    # --extractor-args: iOS 클라이언트 우선 사용 (최대 호환성)
    return [
        '-P', download_path,
        '--retries', '10',
        '--fragment-retries', '10',
        '--sleep-interval', '2',
        '--ignore-errors',
        '--no-warnings',
        '--newline',
        '--no-colors',
        '--extractor-args', 'youtube:player_client=ios,android,web;player_skip=webpage,configs',
        '--progress-template', 'download:%(progress.downloaded_bytes)s/%(progress.total_bytes)s|%(progress.speed)s|%(progress.eta)s|%(progress._percent_str)s'
    ]

def get_video_options(extension='mp4'):
    # 안드로이드 클라이언트를 사용하면서 더 유연한 포맷 선택
    # SABR 스트리밍 문제를 피하기 위해 여러 대체 옵션 제공
    if extension == 'mp4': 
        return [
            '-f', 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best', 
            '--merge-output-format', 'mp4'
        ]
    elif extension == 'mkv': 
        return [
            '-f', 'bestvideo+bestaudio/best', 
            '--merge-output-format', 'mkv'
        ]
    return [
        '-f', 'bestvideo+bestaudio/best[ext=mp4]/best', 
        '--merge-output-format', 'mp4'
    ]

def clean_playlist_url(url):
    return url

class StatusManager:
    def __init__(self):
        self.status_container = st.empty()
        self.total_progress_container = st.empty()
        self.stats_container = st.empty()  # For real-time or final stats
        self.log_expander = st.expander("📜 상세 로그 보기 (클릭)", expanded=False)
        self.log_text = self.log_expander.empty()
        
        self.logs = []
        self.total_downloaded_bytes = 0
        self.current_item_index = 0
        self.total_items = 0
        self.completed_files = set() # 중복 카운팅 방지
        
        # Statistics
        self.stats = {
            'success': 0,
            'skipped': 0,
            'error': 0, # Hidden/Private/Unavailable
            'filtered': 0 # Shorts etc.
        }

    def update_total_status(self):
        if self.total_items > 0:
            with self.total_progress_container.container():
                st.markdown("---")
                st.markdown(f"### 📊 전체 진행 현황 ({self.current_item_index} / {self.total_items})")
                total_progress = self.current_item_index / self.total_items
                st.progress(min(total_progress, 1.0))
                
                # 누적 용량 계산 (MB 단위)
                total_mb = self.total_downloaded_bytes / (1024 * 1024)
                st.write(f"📂 현재까지 누적 용량: **{total_mb:.2f} MB**")

    def update_status(self, progress_str, filename="다운로드 중..."):
        try:
            parts = progress_str.split('|')
            if len(parts) >= 4:
                size_info = parts[0] # downloaded/total
                speed = parts[1]
                eta = parts[2]
                percent_str = parts[3].replace('%', '').strip()
                
                try:
                    progress = float(percent_str) / 100
                except:
                    progress = 0
                
                with self.status_container.container():
                    st.info(f"🎬 **{filename}**")
                    st.progress(min(progress, 1.0))
                    c1, c2, c3 = st.columns(3)
                    c1.metric("속도", speed)
                    c2.metric("남은 시간", "NA" if "NA" in eta else eta)
                    c3.metric("용량 정보", size_info)
        except Exception:
            pass
            
    def add_log(self, msg):
        clean_msg = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', msg).strip()
        if not clean_msg: return
        
        self.logs.append(clean_msg)
        # 실행 중에는 최신 20줄만 보여줘서 렌더링 성능 확보
        self.log_text.code("\n".join(self.logs[-20:]), language="text")

    def increment_stat(self, key):
        if key in self.stats:
            self.stats[key] += 1
            
    def mark_success(self, filename):
        if filename not in self.completed_files:
            self.completed_files.add(filename)
            self.increment_stat('success')

    def show_final_results(self):
        # 최종 통계 및 전체 로그 표시
        st.markdown("---")
        st.success("📝 **작업 요약**")
        
        s = self.stats
        total_processed = s['success'] + s['skipped'] + s['error'] + s['filtered']
        
        cols = st.columns(4)
        cols[0].metric("✅ 완료", s['success'])
        cols[1].metric("⏭️ 건너뜀 (중복)", s['skipped'])
        cols[2].metric("🚫 제외됨 (쇼츠/필터)", s['filtered'])
        cols[3].metric("⚠️ 오류 (비공개/삭제)", s['error'])
        
        # total_items가 0이면(단일 영상 등) 처리된 수로 대체
        total_display = self.total_items if self.total_items > 0 else total_processed
        st.caption(f"총 처리 시도: {total_processed}개 (전체 목록: {total_display}개)")

        # 전체 로그 출력 (복사 가능하도록)
        st.markdown("### 📜 전체 작업 로그")
        st.code("\n".join(self.logs), language="text")


def run_yt_dlp_binary(cmd_list):
    status_mgr = StatusManager()
    
    base_cmd = get_yt_dlp_cmd()
    full_cmd = base_cmd + cmd_list
    
    process = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )

    current_file = "다운로드 준비 중..."
    
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            line = line.strip()
            
            # 순서 정보 감지 ([001/100])
            seq_match = re.search(r'Downloading video (\d+) of (\d+)', line)
            if seq_match:
                status_mgr.current_item_index = int(seq_match.group(1))
                status_mgr.total_items = int(seq_match.group(2))
                status_mgr.update_total_status()

            # 파일명 감지
            if "[download] Destination:" in line:
                current_file = os.path.basename(line.split("Destination:", 1)[1].strip())
                status_mgr.add_log(f"📥 시작: {current_file}")
            
            # 이미 있는 파일 감지 (순서 업데이트를 위해 필요)
            elif "has already been downloaded" in line:
                # [download] FILENAME has already been downloaded
                # 파일명을 추출해서 current_file 업데이트
                try:
                    prefix = "[download] "
                    suffix = " has already been downloaded"
                    if line.startswith(prefix) and line.endswith(suffix):
                        current_file = line[len(prefix):-len(suffix)].strip()
                        current_file = os.path.basename(current_file)
                except: pass
                
                status_mgr.increment_stat('skipped')
                status_mgr.add_log(f"⏭️ 건너뜀 (이전 기록 있음): {current_file}")
            
            # 필터링됨 (쇼츠 등) - Does not pass match filter
            elif "does not pass match filter" in line:
                status_mgr.increment_stat('filtered')
                status_mgr.add_log(f"🚫 제외됨 (필터/쇼츠): {current_file}")

            # 오류/비공개 등
            elif "ERROR:" in line or "Private video" in line or "Video unavailable" in line:
                status_mgr.increment_stat('error')
                status_mgr.add_log(f"⚠️ 오류/비공개: {line}")

            # 진행률 데이터 감지
            elif line.startswith("download:"):
                data = line.replace("download:", "")
                status_mgr.update_status(data, current_file)
                
                # 100% 완료 감지 (커스텀 템플릿 사용 시)
                if "100%" in data:
                     status_mgr.mark_success(current_file)

                try:
                    downloaded_bytes = int(data.split('/')[0])
                except: pass
            
            # 파일 다운로드 완료 감지 (일반 출력 시)
            elif "100%" in line:
                 status_mgr.mark_success(current_file)

            else:
                if not line.startswith("[download]"):
                    status_mgr.add_log(line)
            
            status_mgr.update_total_status()

    # 프로세스 종료 후
    if process.returncode == 0:
        st.success("🎉 모든 작업이 완료되었습니다!")
    else:
        st.warning("⚠️ 일부 작업이 실패했거나 경고가 있었습니다.")
        
    # 최종 결과 및 전체 로그 표시
    status_mgr.show_final_results()

def run_download_process(command_template, url, download_path, include_shorts=False, archive_name=".download_archive.txt"):
    if "list=RD" in url:
        st.error("🚫 유튜브 믹스(Mix) 목록은 다운로드할 수 없습니다. '단일 동영상' 탭을 이용해주세요.")
        return

    sync_archive(download_path, archive_name)

    cmd = []
    cmd.extend(command_template)

    archive_file = get_archive_file(download_path, archive_name)
    cmd.extend(['--download-archive', archive_file])

    if not include_shorts:
        cmd.extend(['--match-filter', 'duration > 180'])

    cmd.append(url)

    run_yt_dlp_binary(cmd)

def run_simple_download(command_template, url, download_path, include_shorts=False, archive_name=".download_archive.txt"):
    run_download_process(command_template, url, download_path, include_shorts, archive_name)

def run_force_download(command_template, url):
    download_path = os.path.expanduser("~")
    # -P 옵션 값 찾기
    if '-P' in command_template:
        idx = command_template.index('-P')
        if idx + 1 < len(command_template):
            download_path = command_template[idx+1]
        
    if "list=" in url:
        url = re.sub(r'[?&]list=[^&]+', '', url)

    cmd = []
    cmd.extend(command_template) # 기본 옵션들
    cmd.append(url)
    
    run_yt_dlp_binary(cmd)

