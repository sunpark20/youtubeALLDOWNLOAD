# 🎬 YouTube ALL DOWNLOADER

Desktop application for downloading entire YouTube channels with smart deduplication and playlist organization.

## ✨ Features

- **Channel Full Download**: Download all videos from a YouTube channel (100+ videos supported)
- **Smart Deduplication**: Automatically remove duplicate videos using Set-based algorithm
- **Local File Checking**: Skip already downloaded files using SHA-256 hash comparison
- **Playlist Organization**: Organize downloads by playlists in separate folders
- **Auto-Update yt-dlp**: Automatically updates yt-dlp on startup for compatibility
- **Multiple Quality Options**: Choose from 360p, 720p, 1080p, or audio-only (MP3)
- **Cross-Platform**: Works on Windows and macOS

## 🏗️ Architecture

- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Backend**: Python 3.11+ with FastAPI
- **Desktop Wrapper**: pywebview
- **YouTube Integration**: yt-dlp + YouTube Data API v3
- **Build**: PyInstaller for standalone executables

## 📋 Requirements

- Python 3.11 or higher
- YouTube Data API v3 key (optional, for channel analysis)

## 🚀 Quick Start

### Development Mode

```bash
# 1. Clone repository
git clone https://github.com/sunpark20/youtubeALLDOWNLOAD.git
cd youtubeALLDOWNLOAD

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set YouTube API key
export YOUTUBE_API_KEY="your_api_key_here"

# 5. Run application
python src/main.py
```

### Building Executables

```bash
# For current platform
pyinstaller --onefile --windowed --name="YouTubeDownloader" src/main.py

# Output: dist/YouTubeDownloader.exe (Windows) or dist/YouTubeDownloader.app (macOS)
```

## 📖 Usage

1. **Launch Application**: Run the executable or `python src/main.py`
2. **Enter Channel URL**: Paste a YouTube channel URL
3. **Configure Options**:
   - Choose quality (360p, 720p, 1080p, audio)
   - Enable playlist organization if needed
   - Set maximum videos to fetch
4. **Analyze**: Click "영상 목록 가져오기" to fetch video list
5. **Download**: Review the list and click "전체 다운로드"

Files are saved to: `~/Downloads/YouTubeDownloader/`

## 🛠️ Development

### Project Structure

```
youtubeALLDOWNLOAD/
├── src/
│   ├── main.py              # Application entry point
│   ├── api/                 # FastAPI server
│   ├── services/            # Core business logic
│   ├── utils/               # Utilities
│   └── frontend/            # Web UI
├── requirements.txt
├── ARCHITECTURE.md          # Detailed architecture
└── DEVELOPMENT_LOG.md       # Development progress
```

### Key Services

- **updater.py**: Auto-update yt-dlp
- **youtube_api.py**: YouTube Data API integration
- **duplicate_filter.py**: Deduplication logic
- **downloader.py**: yt-dlp wrapper

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/channel/analyze` - Analyze channel
- `POST /api/download/extract` - Extract download URL
- `POST /api/updater/update` - Update yt-dlp

## 🧪 Testing

```bash
# Run individual service tests
python src/services/updater.py
python src/services/duplicate_filter.py

# Full integration test
python src/main.py
```

## 📦 Build & Deploy

### GitHub Actions (Automated)

Push to the repository triggers automatic builds for both Windows and macOS:

```bash
git push origin main
```

Artifacts are available in GitHub Actions → Workflow → Artifacts

### Manual Build

```bash
# macOS
pyinstaller --onefile --windowed --name="YouTubeDownloader" --icon=assets/icon.icns src/main.py

# Windows (on Windows machine or VM)
pyinstaller --onefile --windowed --name="YouTubeDownloader" --icon=assets/icon.ico src/main.py
```

## ⚙️ Configuration

Edit `src/utils/config.py` to customize:

- Download directory
- Server host/port
- Default quality
- Maximum videos per request

## 🐛 Troubleshooting

**yt-dlp not updating?**
- Check internet connection
- Run manually: `pip install --upgrade yt-dlp`

**YouTube API errors?**
- Verify API key is set
- Check quota limits (10,000 units/day)

**Downloads failing?**
- Update yt-dlp to latest version
- Check YouTube URL is valid
- Try different quality option

## 📄 License

This project is open source. See LICENSE for details.

## 🤝 Contributing

Contributions welcome! Please check ARCHITECTURE.md and DEVELOPMENT_LOG.md for current status.

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ using Python + FastAPI + pywebview**
