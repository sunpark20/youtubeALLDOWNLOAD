import re

with open('src/api/routes.py', 'r') as f:
    content = f.read()

new_endpoint = """
@router.post("/channel/playlists/analyze", response_model=ChannelAnalyzeResponse)
async def analyze_channel_playlists(request: ChannelAnalyzeRequest):
    \"\"\"Analyze a YouTube channel's playlists and get all videos grouped by playlist\"\"\"
    request.url = normalize_input(request.url)
    if not is_valid_youtube_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        channel_id = None
        channel_name = ''
        videos_list = []
        use_fallback = not youtube_service

        if not use_fallback:
            channel_id = youtube_service.extract_channel_id(request.url)
            if not channel_id:
                username = youtube_service.extract_username(request.url)
                if username:
                    channel_id = youtube_service.get_channel_id_from_username(username)
            
            if channel_id:
                logger.info(f"Analyzing channel playlists via API: {channel_id}")
                # Fetch all playlists
                playlists = youtube_service.get_channel_playlists(channel_id)
                for pl in playlists:
                    pl_videos = youtube_service.get_playlist_videos(pl['id'], request.max_videos)
                    for v in pl_videos:
                        videos_list.append({
                            'id': v['id'],
                            'title': v['title'],
                            'publishedAt': v.get('publishedAt'),
                            'playlist_name': pl['title']
                        })
            else:
                use_fallback = True

        if use_fallback:
            # Fallback for playlists is complex with yt-dlp, we will try to use yt-dlp on the /playlists URL directly
            # which usually yields playlists. Then we extract videos.
            logger.info(f"Using yt-dlp fallback for channel playlists analysis: {request.url}")
            
            import yt_dlp
            # Make sure url ends with /playlists
            url = request.url.rstrip('/')
            if not url.endswith('/playlists'):
                if url.endswith('/videos'):
                    url = url[:-7]
                url += '/playlists'
                
            ydl_opts = {'quiet': True, 'extract_flat': True}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    channel_name = info.get('channel', '') or info.get('uploader', '')
                    channel_id = info.get('channel_id', 'unknown_channel')
                    
                    entries = info.get('entries', [])
                    for pl_entry in entries:
                        pl_title = pl_entry.get('title', 'Unknown Playlist')
                        pl_url = pl_entry.get('url')
                        if pl_url:
                            pl_info = ydl.extract_info(pl_url, download=False)
                            for v_entry in pl_info.get('entries', []):
                                if v_entry and v_entry.get('id'):
                                    videos_list.append({
                                        'id': v_entry['id'],
                                        'title': v_entry.get('title', 'Unknown'),
                                        'playlist_name': pl_title
                                    })
            except Exception as e:
                logger.error(f"yt-dlp fallback failed for playlists: {e}")

        if not videos_list:
            return ChannelAnalyzeResponse(
                success=True,
                channel_id=channel_id,
                message="No playlist videos found"
            )

        total_videos = len(videos_list)

        # Deduplicate - wait, we might have same video in multiple playlists. 
        # If user wants them in separate folders, we SHOULD NOT deduplicate across playlists, 
        # or we only deduplicate exact same video in the exact same playlist.
        # Let's deduplicate by (id, playlist_name)
        unique_vids = []
        seen = set()
        for v in videos_list:
            key = (v['id'], v.get('playlist_name', ''))
            if key not in seen:
                seen.add(key)
                unique_vids.append(v)
                
        videos_list = unique_vids
        unique_videos = len(videos_list)
        duplicates_removed = total_videos - unique_videos

        # Check for already downloaded
        to_download_vids = []
        already_downloaded = 0
        from utils.config import Config
        for v in videos_list:
            safe_chan = channel_name or channel_id or "Unknown Channel"
            safe_pl = v.get('playlist_name') or "Unknown Playlist"
            download_path = Config.get_download_path(safe_chan, safe_pl)
            
            # Check if file exists (duplicate_filter logic for single file)
            # Actually DuplicateFilter expects a list of IDs. We can check manually or use filter.
            # It's easier to use the filter per video.
            res = duplicate_filter.filter_already_downloaded([v], str(download_path))
            if res:
                to_download_vids.append(v)
            else:
                already_downloaded += 1
                
        to_download = len(to_download_vids)

        video_infos = [
            VideoInfo(
                id=v['id'],
                title=v['title'],
                published_at=v.get('publishedAt'),
                playlist_name=v.get('playlist_name')
            )
            for v in to_download_vids
        ]

        source = "yt-dlp" if use_fallback else "YouTube API"
        return ChannelAnalyzeResponse(
            success=True,
            channel_id=channel_id,
            channel_name=channel_name or None,
            total_videos=total_videos,
            unique_videos=unique_videos,
            duplicates_removed=duplicates_removed,
            already_downloaded=already_downloaded,
            to_download=to_download,
            videos=video_infos,
            message=f"Found {to_download} videos to download (via {source})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing channel playlists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""

content = content.replace('@router.post("/playlist/analyze", response_model=PlaylistAnalyzeResponse)', new_endpoint + '\n@router.post("/playlist/analyze", response_model=PlaylistAnalyzeResponse)')

with open('src/api/routes.py', 'w') as f:
    f.write(content)
