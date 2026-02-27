/**
 * YouTube ALL DOWNLOADER - Frontend Application
 *
 * Main JavaScript logic for the desktop application
 */

// API Base URL
const API_BASE = '/api';

// State
let currentVideos = [];
let currentChannelName = '';
let currentPlaylistName = '';
let isAnalyzing = false;
let isDownloading = false;

// DOM Elements
const elements = {
    channelUrl: document.getElementById('channelUrl'),
    maxVideos: document.getElementById('maxVideos'),
    quality: document.getElementById('quality'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    resultsSection: document.getElementById('resultsSection'),
    progressSection: document.getElementById('progressSection'),
    downloadAllBtn: document.getElementById('downloadAllBtn'),
    videoList: document.getElementById('videoList'),

    // Stats
    totalVideos: document.getElementById('totalVideos'),
    uniqueVideos: document.getElementById('uniqueVideos'),
    toDownload: document.getElementById('toDownload'),
    alreadyDownloaded: document.getElementById('alreadyDownloaded'),
    videoCount: document.getElementById('videoCount'),

    // Progress
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    downloadLog: document.getElementById('downloadLog'),

    // Status
    statusText: document.getElementById('statusText'),
    ytdlpVersion: document.getElementById('ytdlpVersion'),

    // Settings
    settingsBtn: document.getElementById('settingsBtn'),
    settingsPanel: document.getElementById('settingsPanel'),
    apiKeyInput: document.getElementById('apiKeyInput'),
    saveApiKeyBtn: document.getElementById('saveApiKeyBtn'),
    deleteApiKeyBtn: document.getElementById('deleteApiKeyBtn'),
    apiKeyMessage: document.getElementById('apiKeyMessage'),
    apiKeyStatus: document.getElementById('apiKeyStatus'),

    // Help
    helpBtn: document.getElementById('helpBtn'),
    helpModal: document.getElementById('helpModal'),
    helpCloseBtn: document.getElementById('helpCloseBtn'),
};

/**
 * Initialize application
 */
async function init() {
    console.log('Initializing YouTube ALL DOWNLOADER...');

    // Load saved API key from localStorage
    const savedApiKey = localStorage.getItem('youtube_api_key');
    if (savedApiKey) {
        try {
            await fetch(`${API_BASE}/settings/api-key`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: savedApiKey }),
            });
        } catch (e) {
            console.error('Failed to restore API key:', e);
        }
    }

    // Check health and settings
    await checkHealth();
    await checkApiKeyStatus();

    // Setup event listeners
    elements.analyzeBtn.addEventListener('click', analyzeUrl);
    elements.downloadAllBtn.addEventListener('click', downloadAll);
    elements.settingsBtn.addEventListener('click', toggleSettings);
    elements.saveApiKeyBtn.addEventListener('click', saveApiKey);
    if (elements.deleteApiKeyBtn) {
        elements.deleteApiKeyBtn.addEventListener('click', deleteApiKey);
    }
    elements.helpBtn.addEventListener('click', () => elements.helpModal.style.display = 'flex');
    elements.helpCloseBtn.addEventListener('click', () => elements.helpModal.style.display = 'none');
    elements.helpModal.addEventListener('click', (e) => {
        if (e.target === elements.helpModal) elements.helpModal.style.display = 'none';
    });

    console.log('Application initialized!');
}

/**
 * Check API health and get version info
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            if (data.ytdlp_version) {
                elements.ytdlpVersion.textContent = `yt-dlp ${data.ytdlp_version}`;
            }
        }

        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

/**
 * Detect URL type and call appropriate analyze endpoint
 */
function detectUrlType(url) {
    if (url.includes('playlist?list=') || url.includes('&list=')) {
        return 'playlist';
    }
    if (url.endsWith('/playlists')) {
        return 'channel_playlists';
    }
    return 'channel';
}

/**
 * Analyze URL (auto-detect channel or playlist)
 */
async function analyzeUrl() {
    const url = elements.channelUrl.value.trim();

    if (!url) {
        alert('YouTube 채널 또는 재생목록 URL을 입력해주세요.');
        return;
    }

    if (isAnalyzing) return;

    const urlType = detectUrlType(url);

    // Update UI
    isAnalyzing = true;
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.querySelector('.btn-text').style.display = 'none';
    elements.analyzeBtn.querySelector('.btn-loader').style.display = 'inline';
    elements.resultsSection.style.display = 'none';
    
    let endpoint = '/channel/analyze';
    if (urlType === 'playlist') {
        endpoint = '/playlist/analyze';
    } else if (urlType === 'channel_playlists') {
        endpoint = '/channel/playlists/analyze';
    }

    try {
        const body = {
            url: url,
            max_videos: parseInt(elements.maxVideos.value),
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '분석 실패');
        }

        if (data.success) {
            displayResults(data);
        } else {
            throw new Error(data.message || '분석 실패');
        }

    } catch (error) {
        console.error('Error analyzing:', error);
        alert(`오류: ${error.message}`);
    } finally {
        isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.querySelector('.btn-text').style.display = 'inline';
        elements.analyzeBtn.querySelector('.btn-loader').style.display = 'none';
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // Update stats
    elements.totalVideos.textContent = data.total_videos;
    elements.uniqueVideos.textContent = data.unique_videos;
    elements.toDownload.textContent = data.to_download;
    elements.alreadyDownloaded.textContent = data.already_downloaded;
    elements.videoCount.textContent = data.videos.length;

    // Store videos and metadata
    currentVideos = data.videos;
    currentChannelName = data.channel_name || '';
    currentPlaylistName = data.playlist_name || '';

    // Display video list
    renderVideoList(data.videos);

    // Show results section
    elements.resultsSection.style.display = 'block';

    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Render video list
 */
function renderVideoList(videos) {
    elements.videoList.innerHTML = '';

    if (videos.length === 0) {
        elements.videoList.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">다운로드할 영상이 없습니다.</div>';
        return;
    }

    videos.forEach((video, index) => {
        const videoItem = document.createElement('div');
        videoItem.className = 'video-item';
        videoItem.innerHTML = `
            <div class="video-info">
                <div class="video-title">${index + 1}. ${escapeHtml(video.title)}</div>
                <div class="video-meta">ID: ${video.id}${video.playlist_name ? ` | 재생목록: ${escapeHtml(video.playlist_name)}` : ''}</div>
            </div>
        `;
        elements.videoList.appendChild(videoItem);
    });
}

/**
 * Download all videos
 */
async function downloadAll() {
    if (currentVideos.length === 0) {
        alert('다운로드할 영상이 없습니다.');
        return;
    }

    if (isDownloading) return;

    if (!confirm(`${currentVideos.length}개의 영상을 다운로드하시겠습니까?`)) {
        return;
    }

    isDownloading = true;
    elements.downloadAllBtn.disabled = true;
    elements.progressSection.style.display = 'block';
    elements.progressSection.scrollIntoView({ behavior: 'smooth' });

    // Clear log
    elements.downloadLog.innerHTML = '';

    const quality = elements.quality.value;
    let completed = 0;
    let failed = 0;

    for (let i = 0; i < currentVideos.length; i++) {
        const video = currentVideos[i];
        const progress = Math.round(((i + 1) / currentVideos.length) * 100);

        // Update progress
        elements.progressFill.style.width = `${progress}%`;
        elements.progressText.textContent = `${i + 1} / ${currentVideos.length} (${progress}%)`;

        try {
            addLog(`⬇️ ${video.title} 다운로드 중...`, 'info');

            const response = await fetch(`${API_BASE}/download/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: video.id,
                    quality: quality,
                    channel_name: currentChannelName || null,
                    playlist_name: video.playlist_name || currentPlaylistName || null,
                }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                completed++;
                addLog(`✅ ${video.title}`, 'success');
            } else {
                throw new Error(data.detail || '다운로드 실패');
            }

        } catch (error) {
            console.error(`Error downloading ${video.title}:`, error);
            failed++;
            addLog(`❌ ${video.title}: ${error.message}`, 'error');
        }
    }

    // Complete
    addLog(`완료! 성공: ${completed}, 실패: ${failed}`, 'info');
    const savePath = currentChannelName
        ? `~/Downloads/YouTubeDownloader/${currentChannelName}/${currentPlaylistName || ''}`
        : '~/Downloads/YouTubeDownloader/';
    addLog(`📁 저장 위치: ${savePath}`, 'info');
    alert(`다운로드 완료!\n성공: ${completed}\n실패: ${failed}\n\n저장 위치: ${savePath}`);

    isDownloading = false;
    elements.downloadAllBtn.disabled = false;
}

/**
 * Add log entry
 */
function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.textContent = message;
    elements.downloadLog.appendChild(entry);

    // Auto-scroll to bottom
    elements.downloadLog.scrollTop = elements.downloadLog.scrollHeight;
}

/**
 * Toggle settings panel
 */
function toggleSettings() {
    const panel = elements.settingsPanel;
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

/**
 * Check API key status from server
 */
async function checkApiKeyStatus() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const data = await response.json();

        if (data.has_api_key) {
            elements.apiKeyStatus.textContent = 'API Key 적용됨';
            elements.apiKeyStatus.className = 'api-key-badge badge-active';
            const savedApiKey = localStorage.getItem('youtube_api_key');
            if (savedApiKey) {
                elements.apiKeyInput.value = savedApiKey;
            }
            elements.apiKeyInput.placeholder = '•••••••••••••••••••••••••••••••• (설정됨)';
            elements.apiKeyMessage.textContent = '현재 API 키가 등록되어 있습니다. 변경하려면 새 키를 입력하세요.';
            elements.apiKeyMessage.className = 'settings-message success';
        } else {
            elements.apiKeyStatus.textContent = '톱니바퀴를 눌러 API 키를 추가하면 더 빠르게 분석할 수 있습니다.';
            elements.apiKeyStatus.className = 'api-key-badge badge-fallback';
            elements.apiKeyInput.placeholder = 'YouTube Data API v3 키 입력';
            elements.apiKeyMessage.textContent = '';
        }
    } catch (error) {
        console.error('Failed to check API key status:', error);
    }
}

/**
 * Save API key
 */
async function saveApiKey() {
    const apiKey = elements.apiKeyInput.value.trim();

    if (!apiKey) {
        elements.apiKeyMessage.textContent = 'API 키를 입력해주세요.';
        elements.apiKeyMessage.className = 'settings-message error';
        return;
    }

    elements.saveApiKeyBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/settings/api-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            localStorage.setItem('youtube_api_key', apiKey);
            elements.apiKeyMessage.textContent = data.message;
            elements.apiKeyMessage.className = 'settings-message success';
            elements.apiKeyInput.value = '';
            await checkApiKeyStatus();
        } else {
            throw new Error(data.detail || data.message || 'API 키 설정 실패');
        }
    } catch (error) {
        elements.apiKeyMessage.textContent = error.message;
        elements.apiKeyMessage.className = 'settings-message error';
    } finally {
        elements.saveApiKeyBtn.disabled = false;
    }
}

/**
 * Delete API key
 */
async function deleteApiKey() {
    if (!confirm('저장된 API 키를 삭제하시겠습니까?')) return;

    elements.deleteApiKeyBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/settings/api-key`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (response.ok && data.success) {
            localStorage.removeItem('youtube_api_key');
            elements.apiKeyInput.value = '';
            elements.apiKeyMessage.textContent = data.message;
            elements.apiKeyMessage.className = 'settings-message success';
            await checkApiKeyStatus();
        } else {
            throw new Error(data.message || 'API 키 삭제 실패');
        }
    } catch (error) {
        elements.apiKeyMessage.textContent = error.message;
        elements.apiKeyMessage.className = 'settings-message error';
    } finally {
        elements.deleteApiKeyBtn.disabled = false;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Delay helper
 */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
