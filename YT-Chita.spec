# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

# 운영체제 판별
is_windows = sys.platform.startswith('win')
is_macos = sys.platform == 'darwin'

# 바이너리(ffmpeg) 설정
if is_macos:
    import shutil
    if os.path.exists('/opt/homebrew/bin/ffmpeg'):       # ARM (Apple Silicon)
        ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
        ffprobe_path = '/opt/homebrew/bin/ffprobe'
    elif os.path.exists('/usr/local/bin/ffmpeg'):        # Intel (Homebrew x86_64)
        ffmpeg_path = '/usr/local/bin/ffmpeg'
        ffprobe_path = '/usr/local/bin/ffprobe'
    else:
        ffmpeg_path = shutil.which('ffmpeg')
        ffprobe_path = shutil.which('ffprobe')

    # ffmpeg 누락 시 빌드 실패 (인텔맥 무음 실패 방지)
    if not ffmpeg_path or not os.path.exists(ffmpeg_path):
        raise SystemExit(
            "\n[ERROR] ffmpeg를 찾을 수 없습니다.\n"
            "  ARM:   brew install ffmpeg  (Apple Silicon)\n"
            "  Intel: arch -x86_64 brew install ffmpeg\n"
        )
    if not ffprobe_path or not os.path.exists(ffprobe_path):
        raise SystemExit(
            "\n[ERROR] ffprobe를 찾을 수 없습니다.\n"
            "  ARM:   brew install ffmpeg  (Apple Silicon)\n"
            "  Intel: arch -x86_64 brew install ffmpeg\n"
        )

    icon_file = 'resource/icon.icns'
    target_arch = 'arm64' if platform.machine() == 'arm64' else 'x86_64'
    binaries = [(ffmpeg_path, '.'), (ffprobe_path, '.')]
    print(f"[Spec] ffmpeg: {ffmpeg_path} (arch={target_arch})")
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
    name='YT-Chita',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    icon=icon_file,
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
    name='YT-Chita',
)

if is_macos:
    app = BUNDLE(
        coll,
        name='YT-Chita.app',
        icon=icon_file,
        bundle_identifier='com.sunpark.YouTubeDownloader',
        version='1.2.2',
        info_plist={
            'CFBundleDisplayName': 'YT Chita',
            'CFBundleName': 'YT Chita',
            'CFBundleShortVersionString': '1.2.2',
            'CFBundleVersion': '1.2.2',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': True,
                'NSAllowsLocalNetworking': True,
            },
        },
    )
