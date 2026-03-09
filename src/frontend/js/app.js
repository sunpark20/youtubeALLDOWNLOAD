/**
 * YouTube ALL DOWNLOADER - Frontend Application
 *
 * Main JavaScript logic for the desktop application
 */

// API Base URL
const API_BASE = '/api';

// Loading messages (Hearthstone-style witty messages)
const LOADING_MESSAGES = [
    '유튜브 서버를 설득하는 중...',
    '인내는 쓰다. 그 열매는 달다.\n― 아리스토텔레스',
    '서버 햄스터가 쳇바퀴를 돌리는 중...',
    '천 리 길도 한 걸음부터.\n― 노자',
    '데이터가 택배 기사를 기다리는 중...',
    '급할수록 돌아가라.\n― 한국 속담',
    '영상 목록이 줄을 서는 중...',
    '시작이 반이다. 지금 반은 했다.',
    '유튜브가 심호흡하는 중...',
    '모든 위대한 일은 느리게 시작된다.\n― 토마스 칼라일',
    '잠깐, 뭔가 대단한 일이 일어나고 있다...',
    '기다림의 미학을 실천하는 중...',
    '서버가 커피를 내리는 중...',
    '좋은 것은 기다리는 자에게 온다.\n― 영국 속담',
    '알고리즘이 워밍업하는 중...',
    '빠른 것보다 정확한 게 낫다.',
    '구글 서버에 정중하게 노크하는 중...',
    '아직 여기 있다. 도망 안 갔다.',
    '위대한 영상에는 위대한 인내가 필요하다.',
    '잠깐이면 된다. 아마도. 거의. 곧.',
];

// State
let currentVideos = [];
let currentChannelName = '';
let currentPlaylistName = '';
let isAnalyzing = false;
let isDownloading = false;
let stopRequested = false;

// DOM Elements
const elements = {
    channelUrl: document.getElementById('channelUrl'),
    quality: document.getElementById('quality'),
    includeShorts: document.getElementById('includeShorts'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    resultsSection: document.getElementById('resultsSection'),
    downloadAllBtn: document.getElementById('downloadAllBtn'),
    videoList: document.getElementById('videoList'),

    // Stats
    totalVideos: document.getElementById('totalVideos'),
    alreadyDownloaded: document.getElementById('alreadyDownloaded'),
    videoCount: document.getElementById('videoCount'),

    // Progress
    progressWrap: document.getElementById('progressWrap'),
    stopDownloadBtn: document.getElementById('stopDownloadBtn'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),

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

    // Complete Modal
    completeModal: document.getElementById('completeModal'),
    completeTitle: document.getElementById('completeTitle'),
    completeSummary: document.getElementById('completeSummary'),
    completePath: document.getElementById('completePath'),
    openFolderBtn: document.getElementById('openFolderBtn'),
    completeCloseBtn: document.getElementById('completeCloseBtn'),
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

    // 키보드 흐름: URL 입력 → Enter → 화질 선택 → Enter → 분석 시작
    elements.channelUrl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            elements.quality.focus();
        }
    });
    elements.quality.addEventListener('change', () => {
        elements.analyzeBtn.focus();
    });
    elements.downloadAllBtn.addEventListener('click', downloadAll);
    elements.stopDownloadBtn.addEventListener('click', () => {
        if (isDownloading) {
            stopRequested = true;
            elements.stopDownloadBtn.disabled = true;
            elements.stopDownloadBtn.style.opacity = '0.5';
            document.getElementById('stopWaitMsg').style.display = 'inline';
        }
    });
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
    document.getElementById('openDownloadFolderBtn').addEventListener('click', () => {
        const savePath = currentChannelName
            ? `~/Downloads/YouTubeDownloader/${currentChannelName}/${currentPlaylistName || ''}`
            : '~/Downloads/YouTubeDownloader/';
        openDownloadFolder(savePath);
    });
    elements.completeCloseBtn.addEventListener('click', () => elements.completeModal.style.display = 'none');
    elements.completeModal.addEventListener('click', (e) => {
        if (e.target === elements.completeModal) elements.completeModal.style.display = 'none';
    });

    // 시작 시 URL 입력창에 포커스
    elements.channelUrl.focus();

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
                // 년도를 2자리로 축약 (2026 → 26)
                const shortVer = data.ytdlp_version.replace(/^20/, '');
                elements.ytdlpVersion.innerHTML = `yt-dlp ${shortVer} <span class="update-link" onclick="location.reload()" title="업데이트 확인">🔄update</span>`;
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
    const loaderEl = elements.analyzeBtn.querySelector('.btn-loader');
    loaderEl.style.display = 'inline-block';
    loaderEl.textContent = '분석 중...';
    elements.resultsSection.style.display = 'none';

    // Show loading toast with rotating messages
    const toast = document.getElementById('loadingToast');
    const toastMsg = document.getElementById('loadingToastMsg');
    let msgIndex = 0;
    toastMsg.textContent = LOADING_MESSAGES[0];
    toastMsg.classList.remove('fade-out');
    toast.style.display = 'flex';

    const msgInterval = setInterval(() => {
        toastMsg.classList.add('fade-out');
        setTimeout(() => {
            msgIndex = (msgIndex + 1) % LOADING_MESSAGES.length;
            toastMsg.textContent = LOADING_MESSAGES[msgIndex];
            toastMsg.classList.remove('fade-out');
        }, 300);
    }, 2000);

    let endpoint = '/channel/analyze';
    if (urlType === 'playlist') {
        endpoint = '/playlist/analyze';
    } else if (urlType === 'channel_playlists') {
        endpoint = '/channel/playlists/analyze';
    }

    try {
        const body = {
            url: url,
        };

        // 채널 분석일 때만 include_shorts 전송
        if (urlType === 'channel') {
            body.include_shorts = elements.includeShorts.checked;
        }

        const response = await fetchWithTimeout(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        }, 600000);  // 10분 타임아웃 (yt-dlp 분석은 오래 걸릴 수 있음)

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
        clearInterval(msgInterval);
        toast.style.display = 'none';
        isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.querySelector('.btn-text').style.display = 'inline';
        loaderEl.style.display = 'none';
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    // Update stats
    elements.totalVideos.textContent = data.total_videos;
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

    // Scroll to results and focus download button
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => elements.downloadAllBtn.focus(), 400);
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
        videoItem.id = `video-row-${index}`;
        videoItem.innerHTML = `
            <div class="video-number">${index + 1}</div>
            <div class="video-info">
                <div class="video-title">${escapeHtml(video.title)}</div>
            </div>
            <div class="video-status" id="video-status-${index}"></div>
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

    isDownloading = true;
    stopRequested = false;
    elements.downloadAllBtn.disabled = true;
    elements.analyzeBtn.disabled = true;

    // Show mini progress bar + stop button
    elements.progressWrap.style.display = 'flex';
    elements.stopDownloadBtn.disabled = false;
    elements.stopDownloadBtn.style.opacity = '1';
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = `0/${currentVideos.length}`;

    const quality = elements.quality.value;
    let completed = 0;
    let skipped = 0;
    let failed = 0;
    let stopped = false;

    for (let i = 0; i < currentVideos.length; i++) {
        // Check stop request before starting next video
        if (stopRequested) {
            stopped = true;
            // Mark remaining videos as stopped
            for (let j = i; j < currentVideos.length; j++) {
                updateVideoRow(j, 'stopped', '중지됨');
            }
            break;
        }

        const video = currentVideos[i];
        const progress = Math.round(((i + 1) / currentVideos.length) * 100);

        // Update mini progress
        elements.progressFill.style.width = `${progress}%`;
        elements.progressText.textContent = `${i + 1}/${currentVideos.length}`;

        // Mark current row as downloading
        updateVideoRow(i, 'downloading', '다운로드 중');

        try {
            const response = await fetchWithTimeout(`${API_BASE}/download/start`, {
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
            }, 600000);  // 10분 타임아웃

            const data = await response.json();

            if (response.ok && data.success) {
                if (data.skipped) {
                    skipped++;
                    updateVideoRow(i, 'skip', '스킵');
                } else {
                    completed++;
                    updateVideoRow(i, 'success', '완료');
                }
            } else {
                throw new Error(data.detail || '다운로드 실패');
            }

        } catch (error) {
            console.error(`Error downloading ${video.title}:`, error);
            failed++;
            updateVideoRow(i, 'error', '실패');
        }
    }

    // Summary via modal
    const parts = [];
    if (completed > 0) parts.push(`성공: ${completed}`);
    if (skipped > 0) parts.push(`스킵: ${skipped}`);
    if (failed > 0) parts.push(`실패: ${failed}`);
    if (stopped) parts.push(`중지됨: ${currentVideos.length - completed - skipped - failed}`);
    const savePath = currentChannelName
        ? `~/Downloads/YouTubeDownloader/${currentChannelName}/${currentPlaylistName || ''}`
        : '~/Downloads/YouTubeDownloader/';

    elements.completeTitle.textContent = stopped ? '다운로드 중지됨' : '다운로드 완료';
    elements.completeSummary.textContent = parts.join(' · ');
    elements.completePath.textContent = savePath;
    elements.openFolderBtn.onclick = () => openDownloadFolder(savePath);
    elements.completeModal.style.display = 'flex';

    isDownloading = false;
    stopRequested = false;
    elements.downloadAllBtn.disabled = false;
    elements.analyzeBtn.disabled = false;
    elements.progressWrap.style.display = 'none';
    document.getElementById('stopWaitMsg').style.display = 'none';
}

/**
 * Update a video row's download status in-place
 */
function updateVideoRow(index, type, statusText) {
    const row = document.getElementById(`video-row-${index}`);
    if (!row) return;

    const numberEl = row.querySelector('.video-number');
    const statusEl = document.getElementById(`video-status-${index}`);

    // Update row state
    row.setAttribute('data-state', type);
    numberEl.className = `video-number video-number-${type}`;
    statusEl.className = `video-status video-status-${type}`;
    statusEl.textContent = statusText;

    // Auto-scroll to current row
    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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
            elements.apiKeyStatus.textContent = 'API 키를 추가하면 더 빠르게 분석할 수 있습니다.';
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
 * Open download folder in system file manager
 */
async function openDownloadFolder(path) {
    try {
        await fetch(`${API_BASE}/open-folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path }),
        });
    } catch (e) {
        console.error('Failed to open folder:', e);
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
 * Fetch with extended timeout (default 10 minutes)
 * Prevents WebKit "Load failed" error for long-running requests
 */
function fetchWithTimeout(url, options = {}, timeoutMs = 600000) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    return fetch(url, {
        ...options,
        signal: controller.signal,
    }).finally(() => clearTimeout(timeout));
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
