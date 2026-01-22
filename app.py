import streamlit as st
import os
import sys
from utils import load_config, save_config, check_system_requirements, update_yt_dlp_binary, sync_archive, resolve_resource_path
from downloader import run_download_process, run_simple_download, run_force_download, get_base_options, get_video_options, AUDIO_FORMAT_OPTIONS, get_subtitle_options

def render_folder_browser():
    st.sidebar.markdown("### 📂 폴더 선택")
    curr = st.session_state['current_browser_path']
    st.sidebar.code(curr)
    c1, c2 = st.sidebar.columns(2)
    if c1.button("⬆️ 상위"):
        p = os.path.dirname(curr)
        if os.path.exists(p):
            st.session_state['current_browser_path'] = p
            st.rerun()
    if c2.button("✅ 확정"):
        st.session_state['download_path'] = curr
        save_config({"download_path": st.session_state['download_path'], "channel_handle": st.session_state['channel_handle'], "include_shorts": st.session_state['include_shorts']})
        st.rerun()
    try:
        items = sorted([d for d in os.listdir(curr) if os.path.isdir(os.path.join(curr, d)) and not d.startswith('.')])
        for d in items:
            if st.sidebar.button(f"📁 {d}", key=f"d_{d}"):
                st.session_state['current_browser_path'] = os.path.join(curr, d)
                st.rerun()
    except: pass

def main():
    st.set_page_config(page_title="Downloader", layout="wide")

    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 400px;
        max-width: 400px;
    }
    </style>
    """, unsafe_allow_html=True)

    check_system_requirements()

    if 'initial_update_checked' not in st.session_state:
        msg_placeholder = st.empty()
        with msg_placeholder.container():
            st.info("⏳ 최신 다운로드 엔진을 확인하고 있습니다. 잠시만 기다려주세요...")
            success, msg = update_yt_dlp_binary()
            if success:
                if "up to date" in msg:
                    st.success(f"✅ 엔진이 최신 버전입니다.")
                else:
                    st.success(f"✅ 엔진 업데이트 완료: {msg}")
            else:
                st.warning(f"⚠️ 엔진 업데이트 확인 실패 (기능은 계속 사용 가능): {msg}")
            import time
            time.sleep(1.5)
        msg_placeholder.empty()
        st.session_state['initial_update_checked'] = True

    if 'download_path' not in st.session_state:
        cfg = load_config()
        st.session_state.update({"download_path": cfg["download_path"], "channel_handle": cfg["channel_handle"], "include_shorts": cfg["include_shorts"], "current_browser_path": cfg["download_path"]})

    if 'archive_synced' not in st.session_state:
        sync_archive(st.session_state['download_path'], ".download_archive_all_videos.txt")
        sync_archive(st.session_state['download_path'], ".download_archive_all_videos_audio.txt")
        sync_archive(st.session_state['download_path'], ".download_archive_all_playlists.txt")
        sync_archive(st.session_state['download_path'], ".download_archive_all_playlists_audio.txt")
        sync_archive(st.session_state['download_path'], ".download_archive_individual_playlist.txt")
        sync_archive(st.session_state['download_path'], ".download_archive_individual_playlist_audio.txt")
        st.session_state['archive_synced'] = True

    st.sidebar.header("설정")

    if st.sidebar.button("🚪 앱 종료", type="secondary", use_container_width=True):
        st.warning("앱을 종료합니다...")
        import time
        time.sleep(0.5)
        os._exit(0)

    st.sidebar.markdown("---")

    with st.sidebar.expander("❓ 채널 핸들"):
        img_path = resolve_resource_path("대문설명.png")
        if os.path.exists(img_path): st.image(img_path)
        else: st.info("예: @song_forest -> song_forest")

    h = st.sidebar.text_input("채널 핸들", value=st.session_state['channel_handle'])
    if h != st.session_state['channel_handle']:
        st.session_state['channel_handle'] = h
        save_config({"download_path": st.session_state['download_path'], "channel_handle": st.session_state['channel_handle'], "include_shorts": st.session_state['include_shorts']})

    st.sidebar.markdown("---")

    st.sidebar.caption("다운로드가 안 될 시 업데이트 해주세요")
    if st.sidebar.button("🚀 엔진 업데이트 (yt-dlp)"):
        with st.spinner("최신 버전으로 업데이트 중..."):
            success, msg = update_yt_dlp_binary()
            if success:
                st.sidebar.success(f"성공: {msg}")
            else:
                st.sidebar.error(f"실패: {msg}")
    
    st.sidebar.markdown("---")
    render_folder_browser()
    st.sidebar.markdown("---")
    st.sidebar.info(f"저장: {st.session_state['download_path']}")
    
    s = st.sidebar.checkbox("쇼츠 포함(3분 이하)", value=st.session_state['include_shorts'])
    if s != st.session_state['include_shorts']:
        st.session_state['include_shorts'] = s
        save_config({"download_path": st.session_state['download_path'], "channel_handle": st.session_state['channel_handle'], "include_shorts": st.session_state['include_shorts']})

    st.sidebar.markdown("---")

    toss_img_path = resolve_resource_path("토스후원.PNG")

    if os.path.exists(toss_img_path):
        import base64
        with open(toss_img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        st.sidebar.markdown(
            f'<a href="supertoss://send?amount=0&bank=KB%EA%B5%AD%EB%AF%BC%EC%9D%80%ED%96%89&accountNo=92682879142&origin=qr" target="_blank">'
            f'<img src="data:image/png;base64,{data}" width="100%">'
            '</a>',
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown("[☕️ 개발자에게 1000원 후원해주기](supertoss://send?amount=0&bank=KB%EA%B5%AD%EB%AF%BC%EC%9D%80%ED%96%89&accountNo=92682879142&origin=qr)")

    with st.sidebar.expander("📖 상세 동작 설명서"):
        st.markdown("""
**다운로드 기록 관리**
- 각 저장 폴더마다 독립적인 기록 유지
- 폴더 A 기록 ≠ 폴더 B 기록

**영상/음성 분리 기록**
- 영상으로 받아도 음성으로 다시 받을 수 있음
- 화질(720p/최고화질)은 동일 영상으로 처리

**모드별 저장 위치**
- 전체 동영상: `채널명/_모든 동영상/` (음성: `_모든 동영상_음성/`)
- 전체 재생목록: `채널명/재생목록명/` (음성: `재생목록명_음성/`)
- 개별 플레이리스트: `플레이리스트/` (음성: `플레이리스트_음성/`)
- 단일 동영상: `개별_영상/` 또는 `개별_음성/`

**중복 방지 규칙**
- 같은 모드 + 같은 유형(영상/음성) 내에서만 중복 체크
- 다른 모드는 별도 기록
""")

    path, shorts, handle = st.session_state['download_path'], st.session_state['include_shorts'], st.session_state['channel_handle']
    base_opts = get_base_options(path)
    default_vid_opts = get_video_options('mp4')
    quality_map = {"mp4 (720p, 모바일폰용)": "mp4", "mkv (최고화질, 원본)": "mkv"}

    tab_options = ["전체 동영상 다운로드", "전체 재생목록 동영상", "개별 플레이 리스트", "단일 동영상"]
    if 'selected_tab' not in st.session_state:
        st.session_state['selected_tab'] = tab_options[0]

    selected_tab = st.selectbox("다운로드 모드 선택", tab_options, index=tab_options.index(st.session_state['selected_tab']), key="tab_selector")
    st.session_state['selected_tab'] = selected_tab

    st.markdown("---")

    if selected_tab == "전체 동영상 다운로드":
        c1, c2 = st.columns(2)
        type_sel_all = c1.radio("유형", ["영상", "음성"], horizontal=True, key="all_v_t")
        ext_all = None
        if type_sel_all == "영상":
            selected_label = c2.selectbox("화질", list(quality_map.keys()), key="all_v_e")
            ext_all = quality_map[selected_label]
        else: c2.write("MP3")

        if st.button("채널 전체 다운로드"):
            url = f"https://www.youtube.com/@{handle}/videos"
            opts = get_video_options(ext_all) if type_sel_all == "영상" else AUDIO_FORMAT_OPTIONS
            folder = "_모든 동영상" if type_sel_all == "영상" else "_모든 동영상_음성"
            archive = ".download_archive_all_videos.txt" if type_sel_all == "영상" else ".download_archive_all_videos_audio.txt"
            cmd = ['-o', f'%(channel)s/{folder}/%(upload_date)s - %(title)s [%(id)s].%(ext)s'] + base_opts + opts
            run_download_process(cmd, url, path, shorts, archive_name=archive)

    elif selected_tab == "전체 재생목록 동영상":
        c1, c2 = st.columns(2)
        type_sel_pl = c1.radio("유형", ["영상", "음성"], horizontal=True, key="all_pl_t")
        ext_pl = None
        if type_sel_pl == "영상":
            selected_label = c2.selectbox("화질", list(quality_map.keys()), key="all_pl_e")
            ext_pl = quality_map[selected_label]
        else: c2.write("MP3")

        if st.button("재생목록 전체 다운로드"):
            url = f"https://www.youtube.com/@{handle}/playlists"
            opts = get_video_options(ext_pl) if type_sel_pl == "영상" else AUDIO_FORMAT_OPTIONS
            folder_suffix = "" if type_sel_pl == "영상" else "_음성"
            archive = ".download_archive_all_playlists.txt" if type_sel_pl == "영상" else ".download_archive_all_playlists_audio.txt"
            cmd = ['-o', f'%(channel)s/%(playlist)s{folder_suffix}/%(upload_date)s - %(title)s [%(id)s].%(ext)s'] + base_opts + opts
            run_simple_download(cmd, url, path, shorts, archive_name=archive)

    elif selected_tab == "개별 플레이 리스트":
        u = st.text_input("PL URL")
        c1, c2 = st.columns(2)
        type_Sel = c1.radio("유형", ["영상", "음성"], horizontal=True, key="pl_t")
        ext = None

        if type_Sel == "영상":
            selected_label = c2.selectbox("화질", list(quality_map.keys()), key="pl_e")
            ext = quality_map[selected_label]
        else: c2.write("MP3")

        if st.button("PL 다운로드"):
            if not u or "list=" not in u: st.error("잘못된 링크"); st.stop()
            opts = get_video_options(ext) if type_Sel == "영상" else AUDIO_FORMAT_OPTIONS
            folder = "플레이리스트" if type_Sel == "영상" else "플레이리스트_음성"
            archive = ".download_archive_individual_playlist.txt" if type_Sel == "영상" else ".download_archive_individual_playlist_audio.txt"
            cmd = ['-o', f'{folder}/%(uploader)s_%(playlist)s/%(upload_date)s - %(title)s [%(id)s].%(ext)s'] + base_opts + opts
            run_download_process(cmd, u, path, shorts, archive_name=archive)

    elif selected_tab == "단일 동영상":
        u = st.text_input("URL")
        c1, c2 = st.columns(2)
        type_Sel = c1.radio("유형", ["영상", "음성"], horizontal=True, key="s_t")
        ext = None
        if type_Sel == "영상":
            selected_label = c2.selectbox("화질", list(quality_map.keys()), key="s_e")
            ext = quality_map[selected_label]
        else: c2.write("MP3")

        download_subs = False
        if type_Sel == "영상":
            download_subs = st.checkbox("자막 다운로드 (가능한 모든 언어)", key="s_subs")

        if st.button("다운로드"):
            if not u: st.warning("URL 필요"); st.stop()
            opts = get_video_options(ext) if type_Sel == "영상" else AUDIO_FORMAT_OPTIONS
            folder = "개별_영상" if type_Sel == "영상" else "개별_음성"
            cmd = ['-o', f'{folder}/%(upload_date)s - %(title)s [%(id)s].%(ext)s', '--no-playlist'] + base_opts + opts
            if download_subs and type_Sel == "영상":
                cmd.extend(get_subtitle_options())
            run_force_download(cmd, u)

if __name__ == "__main__":
    main()