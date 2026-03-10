# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

# 운영체제 판별
is_windows = sys.platform.startswith('win')
is_macos = sys.platform == 'darwin'

# 바이너리(ffmpeg) 설정
if is_macos:
    ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
    ffprobe_path = '/opt/homebrew/bin/ffprobe'
    # 만약 Homebrew 경로에 없으면 현재 디렉토리에서 찾기 (CI 환경 대비)
    if not os.path.exists(ffmpeg_path):
        ffmpeg_path = 'ffmpeg'
        ffprobe_path = 'ffprobe'
    
    icon_file = 'resource/icon.icns'
    target_arch = 'arm64' if platform.machine() == 'arm64' else 'x86_64'
    binaries = [(ffmpeg_path, '.'), (ffprobe_path, '.')]
else:
    # Windows/Linux용 설정
    ffmpeg_path = 'ffmpeg.exe' if is_windows else 'ffmpeg'
    ffprobe_path = 'ffprobe.exe' if is_windows else 'ffprobe'
    icon_file = 'resource/icon.ico' if os.path.exists('resource/icon.ico') else None
    target_arch = None # Windows는 기본 아키텍처 사용
    binaries = [] # Windows에서는 환경변수 PATH를 활용하거나 별도 포함 권장

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('src/frontend', 'src/frontend'),
        ('resource', 'resource')  # 사운드 파일 포함
    ],
    hiddenimports=[
        'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors', 'fastapi.staticfiles', 'fastapi.responses',
        'starlette', 'starlette.routing', 'starlette.middleware', 'starlette.middleware.cors', 'starlette.responses', 'starlette.staticfiles', 'starlette.exceptions', 'starlette.formparsers', 'starlette.status',
        'uvicorn', 'uvicorn.config', 'uvicorn.main', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
        'anyio', 'anyio._backends', 'anyio._backends._asyncio',
        'pydantic', 'pydantic.deprecated', 'pydantic.deprecated.decorator',
        'webview', 'yt_dlp', 'httptools', 'h11', 'python_multipart', 'multipart',
        'email.mime.multipart', 'email.mime.text', 'email.mime.message',
        'typing_extensions', 'aiofiles', 'requests', 'charset_normalizer', 'httplib2',
        'google.auth', 'google.auth.transport.requests', 'google_auth_oauthlib', 'googleapiclient', 'googleapiclient.discovery'
    ] + (['AppKit', 'Foundation', 'WebKit', 'objc', 'PyObjCTools'] if is_macos else []),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file='entitlements.plist' if is_macos else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='YouTubeDownloader',
)

if is_macos:
    app = BUNDLE(
        coll,
        name='YouTubeDownloader.app',
        icon=icon_file,
        bundle_identifier='com.sunpark.YouTubeDownloader',
        version='1.1.4',
        info_plist={
            'CFBundleDisplayName': 'YouTube BULK DOWNLOADER',
            'CFBundleName': 'YouTubeDownloader',
            'CFBundleShortVersionString': '1.1.4',
            'CFBundleVersion': '1.1.4',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': True,
                'NSAllowsLocalNetworking': True,
            },
        },
    )
