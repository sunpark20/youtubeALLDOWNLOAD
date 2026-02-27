/**
 * YouTube ALL DOWNLOADER - Frontend Application
 *
 * Main JavaScript logic for the desktop application
 */

// API Base URL
const API_BASE = '/api';

// State
let currentVideos = [];
let isAnalyzing = false;
let isDownloading = false;

// DOM Elements
const elements = {
    channelUrl: document.getElementById('channelUrl'),
    includePlaylists: document.getElementById('includePlaylists'),
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
    apiKeyMessage: document.getElementById('apiKeyMessage'),
    apiKeyStatus: document.getElementById('apiKeyStatus'),
};

/**
 * Initialize application
 */
async function init() {
    console.log('Initializing YouTube ALL DOWNLOADER...');

    // Check health and settings
    await checkHealth();
    await checkApiKeyStatus();

    // Setup event listeners
    elements.analyzeBtn.addEventListener('click', analyzeChannel);
    elements.downloadAllBtn.addEventListener('click', downloadAll);
    elements.settingsBtn.addEventListener('click', toggleSettings);
    elements.saveApiKeyBtn.addEventListener('click', saveApiKey);

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
            elements.statusText.textContent = '준비 완료';
            elements.statusText.style.color = '#28a745';

            if (data.ytdlp_version) {
                elements.ytdlpVersion.textContent = `yt-dlp ${data.ytdlp_version}`;
            }
        }

        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
        elements.statusText.textContent = '서버 연결 실패';
        elements.statusText.style.color = '#dc3545';
    }
}

/**
 * Analyze YouTube channel
 */
async function analyzeChannel() {
    const url = elements.channelUrl.value.trim();

    if (!url) {
        alert('YouTube 채널 URL을 입력해주세요.');
        return;
    }

    if (isAnalyzing) return;

    // Update UI
    isAnalyzing = true;
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.querySelector('.btn-text').style.display = 'none';
    elements.analyzeBtn.querySelector('.btn-loader').style.display = 'inline';
    elements.resultsSection.style.display = 'none';
    elements.statusText.textContent = '분석 중...';

    try {
        const response = await fetch(`${API_BASE}/channel/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                include_playlists: elements.includePlaylists.checked,
                max_videos: parseInt(elements.maxVideos.value),
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '분석 실패');
        }

        if (data.success) {
            displayResults(data);
            elements.statusText.textContent = '분석 완료';
        } else {
            throw new Error(data.message || '분석 실패');
        }

    } catch (error) {
        console.error('Error analyzing channel:', error);
        alert(`오류: ${error.message}`);
        elements.statusText.textContent = '오류 발생';
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

    // Store videos
    currentVideos = data.videos;

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
                <div class="video-meta">ID: ${video.id}</div>
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
            // Extract download URL
            const response = await fetch(`${API_BASE}/download/extract`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_id: video.id,
                    quality: quality,
                }),
            });

            const data = await response.json();

            if (data.success && data.formats[quality]) {
                // Trigger download
                const downloadUrl = data.formats[quality];
                const filename = `${video.title}.mp4`; // Will be determined by browser

                // Create download link
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = filename;
                a.click();

                completed++;
                addLog(`✅ ${video.title}`, 'success');

                // Delay between downloads
                await delay(500);
            } else {
                throw new Error('다운로드 URL을 가져올 수 없습니다');
            }

        } catch (error) {
            console.error(`Error downloading ${video.title}:`, error);
            failed++;
            addLog(`❌ ${video.title}: ${error.message}`, 'error');
        }
    }

    // Complete
    addLog(`완료! 성공: ${completed}, 실패: ${failed}`, 'info');
    alert(`다운로드 완료!\n성공: ${completed}\n실패: ${failed}`);

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
            elements.apiKeyStatus.textContent = 'API Key ✓';
            elements.apiKeyStatus.className = 'api-key-badge badge-active';
        } else {
            elements.apiKeyStatus.textContent = 'yt-dlp 모드';
            elements.apiKeyStatus.className = 'api-key-badge badge-fallback';
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
