# YouTube ALL DOWNLOADER - Architecture Design

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Frontend (HTML/CSS/JavaScript)             │    │
│  │  - UI Components                                   │    │
│  │  - User Input Handling                             │    │
│  │  - Progress Display                                │    │
│  │  - File Management UI                              │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │ HTTP/WebSocket                          │
│  ┌────────────────▼───────────────────────────────────┐    │
│  │         Backend (Python + FastAPI)                 │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  API Server (FastAPI + Uvicorn)             │  │    │
│  │  │  - REST API Endpoints                       │  │    │
│  │  │  - SSE for real-time updates                │  │    │
│  │  │  - Static file serving                      │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  YouTube Service                            │  │    │
│  │  │  - YouTube Data API v3 integration          │  │    │
│  │  │  - Channel video list retrieval             │  │    │
│  │  │  - Playlist management                      │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  Downloader Service (yt-dlp wrapper)        │  │    │
│  │  │  - Auto-update yt-dlp on startup            │  │    │
│  │  │  - Download URL extraction                  │  │    │
│  │  │  - Format selection                         │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  Duplicate Filter Service                   │  │    │
│  │  │  - Video ID deduplication (Set-based)       │  │    │
│  │  │  - Local file hash checking (SHA-256)       │  │    │
│  │  │  - Skip already downloaded files            │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────────────────────────────────────┐  │    │
│  │  │  File Manager Service                       │  │    │
│  │  │  - Folder structure creation                │  │    │
│  │  │  - File path management                     │  │    │
│  │  │  - Playlist-based organization              │  │    │
│  │  └─────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Desktop Window (pywebview)                  │    │
│  │  - Native window wrapper                           │    │
│  │  - Cross-platform (Windows/Mac)                    │    │
│  │  - Embedded browser view                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with Flexbox/Grid
- **Vanilla JavaScript**: No framework dependencies
- **Fetch API**: HTTP requests to backend
- **EventSource**: Server-Sent Events for real-time updates

### Backend
- **Python 3.11+**: Main programming language
- **FastAPI 0.109+**: Modern async web framework
- **Uvicorn**: ASGI server
- **yt-dlp**: YouTube download engine (auto-updated)
- **google-api-python-client**: YouTube Data API v3
- **hashlib**: File duplicate detection (SHA-256)

### Desktop Wrapper
- **pywebview 5.0+**: Native window wrapper
- **PyInstaller 6.3+**: Build standalone executables

### Development Tools
- **Git**: Version control
- **GitHub Actions**: CI/CD for multi-platform builds

## 📂 Project Structure

```
youtubeALLDOWNLOAD/
├── .github/
│   └── workflows/
│       └── build.yml                 # Auto build for Windows/Mac
│
├── src/
│   ├── main.py                       # Application entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py                 # FastAPI server setup
│   │   ├── routes.py                 # API endpoints
│   │   └── models.py                 # Pydantic models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube_api.py            # YouTube Data API service
│   │   ├── downloader.py             # yt-dlp wrapper
│   │   ├── updater.py                # yt-dlp auto-updater
│   │   ├── duplicate_filter.py       # Deduplication logic
│   │   └── file_manager.py           # File/folder management
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration
│   │   ├── logger.py                 # Logging setup
│   │   └── validators.py             # Input validation
│   │
│   └── frontend/
│       ├── index.html                # Main UI
│       ├── css/
│       │   └── style.css             # Styles
│       └── js/
│           ├── app.js                # Main frontend logic
│           └── api-client.js         # API communication
│
├── assets/
│   ├── icon.icns                     # macOS icon
│   └── icon.ico                      # Windows icon
│
├── tests/
│   ├── test_youtube_api.py
│   ├── test_downloader.py
│   └── test_duplicate_filter.py
│
├── requirements.txt                  # Python dependencies
├── .gitignore
├── README.md
└── ARCHITECTURE.md                   # This file
```

## 🔄 Data Flow

### 1. Application Startup
```
User launches app
    ↓
pywebview creates native window
    ↓
FastAPI server starts (background thread)
    ↓
yt-dlp auto-update check
    ↓
Frontend loads in webview
```

### 2. Channel Download Flow
```
User inputs YouTube channel URL
    ↓
Frontend → POST /api/channel/analyze
    ↓
YouTube API: Get all video IDs from channel
    ↓
Deduplication: Remove duplicate video IDs (Set)
    ↓
Local file check: Skip already downloaded (SHA-256)
    ↓
Frontend ← SSE: Real-time progress updates
    ↓
For each video:
    yt-dlp extracts download URL
    Frontend receives direct download link
    User's browser downloads to local PC
    ↓
Complete: Display summary
```

### 3. Duplicate Detection Strategy
```
Step 1: API-level deduplication
- Use Set data structure for video IDs
- O(1) lookup time
- Remove duplicates before yt-dlp calls

Step 2: Local file checking
- Scan download directory
- Calculate SHA-256 hash for existing files
- Store in dictionary: {video_id: hash}
- Skip if video_id already exists

Result: Fast, efficient deduplication
```

## 🚀 Key Features

### Core Features (Phase 1)
1. **YouTube Channel Full Download**
   - Get all videos from a channel
   - Support for 100+ videos
   - Automatic pagination handling

2. **Playlist-based Organization**
   - Separate folders for each playlist
   - "All Videos" folder for channel uploads
   - Hierarchical structure

3. **Smart Duplicate Removal**
   - API-level: Set-based deduplication
   - File-level: SHA-256 hash comparison
   - Fast detection algorithm

4. **yt-dlp Auto-Update**
   - Check for updates on startup
   - Auto-install latest version
   - Ensure compatibility with YouTube

5. **Real-time Progress**
   - Server-Sent Events (SSE)
   - Live progress bar
   - Per-video status tracking

6. **Cross-platform Support**
   - Windows: .exe
   - macOS: .app
   - Native look and feel

## 📊 API Endpoints

### Health & Status
- `GET /` - Frontend HTML
- `GET /api/health` - Health check
- `GET /api/version` - App & yt-dlp version

### YouTube Operations
- `POST /api/channel/analyze` - Analyze channel, return video list
- `POST /api/playlist/analyze` - Analyze playlist
- `POST /api/download/extract` - Extract download URL for video
- `GET /api/progress/stream` - SSE endpoint for progress

### System
- `POST /api/updater/check` - Check yt-dlp updates
- `POST /api/updater/update` - Update yt-dlp

## 🔐 Security Considerations

1. **No credential storage**: YouTube API key in environment variable
2. **Local-only server**: FastAPI binds to 127.0.0.1 only
3. **Input validation**: Validate all YouTube URLs
4. **Rate limiting**: Prevent API abuse (future)

## 🧪 Testing Strategy

1. **Unit Tests**: Each service independently
2. **Integration Tests**: API endpoints
3. **Manual Tests**: Real YouTube channels
4. **Platform Tests**: Windows & macOS builds

## 📈 Performance Targets

- **Startup time**: < 3 seconds
- **yt-dlp update**: < 10 seconds
- **100 videos analysis**: < 30 seconds
- **Deduplication**: < 1 second (100 videos)
- **Memory usage**: < 200 MB

## 🎯 Development Phases

### Phase 1: Core Desktop App (Current)
- ✅ Architecture design
- 🔄 Basic structure setup
- ⏳ yt-dlp auto-updater
- ⏳ YouTube API integration
- ⏳ Duplicate filter
- ⏳ Basic UI
- ⏳ pywebview integration
- ⏳ GitHub Actions build

### Phase 2: Enhanced Features
- Advanced filtering
- Download history database
- Resume interrupted downloads
- Batch operations

### Phase 3: Web Version
- Lightweight web interface
- Limited features (1-10 videos)
- Oracle Cloud deployment

---

**Document Version**: 1.0
**Last Updated**: 2026-02-13
**Status**: ✅ Complete
