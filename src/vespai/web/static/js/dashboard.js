// VespAI Dashboard JavaScript
// Author: Jakob Zeise (Zeise Digital)

// Translations
const translations = {
    en: {
        'live': 'Live',
        'frames-processed': 'Frames Processed',
        'total-detections': 'Total Detections',
        'vespa-velutina': 'Vespa Velutina',
        'vespa-crabro': 'Vespa Crabro', 
        'bee-class': 'Bee',
        'wasp-class': 'Unknown',
        'sms-alerts': 'SMS Alerts',
        'sms-costs': 'SMS Costs',
        'live-detection-feed': 'Live Detection Feed',
        'fullscreen': 'Fullscreen',
        'detection-log': 'Detection Log',
        'cpu-temp': 'CPU Temp',
        'cpu-usage': 'CPU Usage',
        'ram-usage': 'RAM Usage',
        'uptime': 'Uptime',
        'contact': 'Contact',
        'visit-website': 'Visit Website',
        'footer-headline': 'Modern & Effective Apps for Your Business',
        'footer-tagline': 'Empowering companies to thrive in the digital landscape through innovative solutions',
        'chart-title-24h': 'Detections per Hour (Last 24h)',
        'chart-title-4h': 'Detections per 4-Hour Block (Last 24h)',
        'inference-chart-title': 'Recent Inference Time per Image',
        'cpu-temp-inline': 'CPU Temp',
        'inference-avg-inline': 'Avg',
        'inference-min-inline': 'Min',
        'inference-max-inline': 'Max',
        'asian-hornet': 'Asian Hornet',
        'european-hornet': 'European Hornet',
        'uptime-prefix': 'Uptime:',
        'per-hour': '/h',
        'fps-suffix': 'FPS',
        'source-prefix': 'Source',
        'last-detection-preview': 'Last Detection Image',
        'dataset-mode': 'DATASET',
        'waiting': 'waiting...',
        'model-prefix': 'Model',
        'switch-input-failed': 'Failed to switch input source.',
        'insights': 'Insights',
        'perf-breakdown': 'Performance Breakdown',
        'capture': 'Capture',
        'inference': 'Inference',
        'postprocess': 'Postprocess',
        'detected': 'detected',
        'confidence': 'confidence'
    },
    de: {
        'live': 'Live',
        'frames-processed': 'Bilder Verarbeitet',
        'total-detections': 'Gesamt Erkennungen',
        'vespa-velutina': 'Vespa Velutina',
        'vespa-crabro': 'Vespa Crabro',
        'bee-class': 'Biene',
        'wasp-class': 'Unbekannt',
        'sms-alerts': 'SMS Warnungen',
        'sms-costs': 'SMS Kosten',
        'live-detection-feed': 'Live Erkennungs-Feed',
        'fullscreen': 'Vollbild',
        'detection-log': 'Erkennungsprotokoll',
        'cpu-temp': 'CPU Temperatur',
        'cpu-usage': 'CPU Auslastung',
        'ram-usage': 'RAM Auslastung',
        'uptime': 'Laufzeit',
        'contact': 'Kontakt',
        'visit-website': 'Website Besuchen',
        'footer-headline': 'Moderne & Effektive Apps für Ihr Unternehmen',
        'footer-tagline': 'Wir unterstützen Unternehmen, in der digitalen Welt durch innovative Lösungen zu gedeihen',
        'chart-title-24h': 'Erkennungen pro Stunde (Letzte 24h)',
        'chart-title-4h': 'Erkennungen pro 4-Stunden-Block (Letzte 24h)',
        'inference-chart-title': 'Jüngste Inferenzzeit pro Bild',
        'cpu-temp-inline': 'CPU Temperatur',
        'inference-avg-inline': 'Ø',
        'inference-min-inline': 'Min',
        'inference-max-inline': 'Max',
        'asian-hornet': 'Asiatische Hornisse',
        'european-hornet': 'Europäische Hornisse',
        'uptime-prefix': 'Laufzeit:',
        'per-hour': '/h',
        'fps-suffix': 'FPS',
        'source-prefix': 'Quelle',
        'last-detection-preview': 'Letztes Erkennungsbild',
        'dataset-mode': 'DATENSATZ',
        'waiting': 'warte...',
        'model-prefix': 'Modell',
        'switch-input-failed': 'Eingabequelle konnte nicht gewechselt werden.',
        'insights': 'Einblicke',
        'perf-breakdown': 'Leistungsaufschlüsselung',
        'capture': 'Erfassung',
        'inference': 'Inferenz',
        'postprocess': 'Nachverarbeitung',
        'detected': 'erkannt',
        'confidence': 'Sicherheit'
    },
    fr: {
        'live': 'Direct',
        'frames-processed': 'Images traitées',
        'total-detections': 'Détections totales',
        'vespa-velutina': 'Vespa Velutina',
        'vespa-crabro': 'Vespa Crabro',
        'bee-class': 'Abeille',
        'wasp-class': 'Inconnu',
        'sms-alerts': 'Alertes SMS',
        'sms-costs': 'Coûts SMS',
        'live-detection-feed': 'Flux de détection en direct',
        'fullscreen': 'Plein écran',
        'detection-log': 'Journal de détection',
        'cpu-temp': 'Température CPU',
        'cpu-usage': 'Utilisation CPU',
        'ram-usage': 'Utilisation RAM',
        'uptime': 'Temps de fonctionnement',
        'chart-title-24h': 'Détections par heure (24 dernières h)',
        'chart-title-4h': 'Détections par tranche de 4 h (24 dernières h)',
        'inference-chart-title': 'Temps d’inférence récent par image',
        'cpu-temp-inline': 'Température CPU',
        'inference-avg-inline': 'Moy',
        'inference-min-inline': 'Min',
        'inference-max-inline': 'Max',
        'asian-hornet': 'Frelon asiatique',
        'european-hornet': 'Frelon européen',
        'uptime-prefix': 'Temps de fonctionnement :',
        'per-hour': '/h',
        'fps-suffix': 'FPS',
        'source-prefix': 'Source',
        'last-detection-preview': 'Dernière image détectée',
        'dataset-mode': 'JEU DE DONNÉES',
        'waiting': 'en attente...',
        'model-prefix': 'Modèle',
        'switch-input-failed': 'Impossible de changer la source d’entrée.',
        'insights': 'Insights',
        'perf-breakdown': 'Répartition des performances',
        'capture': 'Capture',
        'inference': 'Inférence',
        'postprocess': 'Post-traitement',
        'detected': 'erkannt',
        'confidence': 'confiance'
    }
};

// Current language
let currentLang = localStorage.getItem('vespai-language') || 'en';

function getDashboardWebConfig() {
    const body = document.body || {};
    const data = body.dataset || {};

    const parseIntOr = (value, fallback) => {
        const parsed = Number.parseInt(value, 10);
        return Number.isFinite(parsed) ? parsed : fallback;
    };

    return {
        webPreviewWidth: parseIntOr(data.webPreviewWidth, 960),
        webPreviewHeight: parseIntOr(data.webPreviewHeight, 540),
        liveStreamQuality: parseIntOr(data.liveStreamQuality, 72),
        currentFrameQuality: parseIntOr(data.currentFrameQuality, 82),
    };
}

const webConfig = getDashboardWebConfig();

// Custom orange neon cursor
let cursor = null;

// Translation functions
function translatePage() {
    const elements = document.querySelectorAll('[data-key]');
    elements.forEach(element => {
        const key = element.getAttribute('data-key');
        if (translations[currentLang] && translations[currentLang][key]) {
            element.textContent = translations[currentLang][key];
        }
    });
    
    // Update language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-lang') === currentLang) {
            btn.classList.add('active');
        }
    });
}

function switchLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('vespai-language', lang);
    translatePage();
    updateSourceToggleBadge(currentInputMode);
}

let isSwitchingSource = false;
let sourceToggleInitialized = false;
let currentInputMode = 'camera';
let currentDatasetPath = '';
let lastRenderedInputMode = null;
let mainFeedInterval = null;
let cameraTogglesInitialized = false;
let cameraAliases = { camera1: 'Camera 1', camera2: 'Camera 2' };
let cameraEnabledState = { camera1: true, camera2: false };
let cameraAvailableState = { camera1: true, camera2: false };
const cameraToggleBusy = { camera1: false, camera2: false };
const CAMERA_STALL_THRESHOLD_S = 3.0;
const CAMERA_OFFLINE_THRESHOLD_S = 15.0;
let insightsOpen = false;
let insightsBusy = false;
let lastInsightsFetchTs = 0;
const INSIGHTS_REFRESH_MS = 5000;

function applyCameraAliases(rawAliases) {
    const aliases = rawAliases || {};
    const sanitizeAlias = (value, fallback) => {
        const alias = String(value || '').trim();
        return (alias || fallback).slice(0, 16);
    };

    cameraAliases = {
        camera1: sanitizeAlias(aliases.camera1, 'Camera 1'),
        camera2: sanitizeAlias(aliases.camera2, 'Camera 2'),
    };

    const camera1Title = document.getElementById('camera1-title');
    const camera2Title = document.getElementById('camera2-title');
    if (camera1Title) camera1Title.textContent = cameraAliases.camera1;
    if (camera2Title) camera2Title.textContent = cameraAliases.camera2;
}

function formatInsightPct(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
        return '0.0%';
    }
    return `${numeric.toFixed(1)}%`;
}

function formatInsightMs(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
        return '0.0 ms';
    }
    return `${numeric.toFixed(1)} ms`;
}

function applyInsightSection(sectionName, pct, avgMs) {
    const pctEl = document.getElementById(`insight-${sectionName}-pct`);
    const msEl = document.getElementById(`insight-${sectionName}-ms`);
    const barEl = document.getElementById(`insight-${sectionName}-bar`);

    if (pctEl) {
        pctEl.textContent = formatInsightPct(pct);
    }
    if (msEl) {
        msEl.textContent = formatInsightMs(avgMs);
    }
    if (barEl) {
        const width = Math.max(0, Math.min(100, Number(pct) || 0));
        barEl.style.width = `${width}%`;
    }
}

function renderInsightsBreakdown(data) {
    const percentages = data && data.percentages ? data.percentages : {};
    const averages = data && data.avg_ms_per_sample ? data.avg_ms_per_sample : {};

    applyInsightSection('capture', percentages.capture, averages.capture);
    applyInsightSection('inference', percentages.inference, averages.inference);
    applyInsightSection('postprocess', percentages.postprocess, averages.postprocess);
    applyInsightSection('web', percentages.web, averages.web);

    const windowEl = document.getElementById('insights-window');
    const samplesEl = document.getElementById('insights-samples');
    if (windowEl) {
        const windowSeconds = Number(data.window_seconds);
        windowEl.textContent = `${Number.isFinite(windowSeconds) ? Math.round(windowSeconds) : 60}s window`;
    }
    if (samplesEl) {
        const sampleCount = Number(data.sample_count) || 0;
        samplesEl.textContent = `${sampleCount} samples`;
    }
}

async function refreshInsights(force = false) {
    if (!insightsOpen && !force) {
        return;
    }
    if (insightsBusy) {
        return;
    }
    const now = Date.now();
    if (!force && (now - lastInsightsFetchTs) < INSIGHTS_REFRESH_MS) {
        return;
    }

    insightsBusy = true;
    try {
        const response = await fetch('/api/perf_breakdown?window_s=60');
        const data = await response.json();
        if (!response.ok || data.success === false) {
            return;
        }
        renderInsightsBreakdown(data);
        lastInsightsFetchTs = Date.now();
    } catch (error) {
        console.error('VespAI Dashboard: Failed to fetch insights breakdown:', error);
    } finally {
        insightsBusy = false;
    }
}

function initInsightsPanel() {
    const toggleButton = document.getElementById('insights-toggle');
    const panel = document.getElementById('insights-panel');
    if (!toggleButton || !panel) {
        return;
    }

    toggleButton.addEventListener('click', function() {
        insightsOpen = !insightsOpen;
        panel.style.display = insightsOpen ? 'block' : 'none';
        toggleButton.classList.toggle('active', insightsOpen);
        if (insightsOpen) {
            refreshInsights(true);
        }
    });
}

function cameraStateHasKey(state, cameraId) {
    return state && Object.prototype.hasOwnProperty.call(state, cameraId);
}

function setCameraToggleAvailability(cameraId, available) {
    const toggle = document.getElementById(`${cameraId}-toggle`);
    if (!toggle) {
        return;
    }

    const isAvailable = !!available;
    if (cameraId === 'camera1') {
        toggle.disabled = false;
        toggle.removeAttribute('title');
        return;
    }

    toggle.disabled = !isAvailable;
    if (isAvailable) {
        toggle.removeAttribute('title');
    } else {
        toggle.title = 'Camera 2 is not configured in the active runtime profile';
    }
}

function applyCameraStateFromServer(cameraEnabled = {}, cameraModes = {}) {
    cameraAvailableState.camera1 = true;
    cameraAvailableState.camera2 = cameraStateHasKey(cameraModes, 'camera2') || cameraStateHasKey(cameraEnabled, 'camera2');

    cameraEnabledState.camera1 = cameraStateHasKey(cameraEnabled, 'camera1')
        ? cameraEnabled.camera1 !== false
        : true;

    if (cameraAvailableState.camera2) {
        cameraEnabledState.camera2 = cameraStateHasKey(cameraEnabled, 'camera2')
            ? cameraEnabled.camera2 !== false
            : cameraEnabledState.camera2 !== false;
    } else {
        cameraEnabledState.camera2 = false;
    }

    setCameraToggleAvailability('camera1', cameraAvailableState.camera1);
    setCameraToggleAvailability('camera2', cameraAvailableState.camera2);
    setCameraToggleVisualState('camera1', cameraEnabledState.camera1);
    setCameraToggleVisualState('camera2', cameraEnabledState.camera2);
}

function formatFrameAge(ageValue) {
    const age = Number(ageValue);
    if (!Number.isFinite(age) || age < 0) {
        return '-';
    }
    return `${age.toFixed(1)}s`;
}

function deriveCameraHealth(cameraStats) {
    const stats = cameraStats || {};
    const status = String(stats.status || '').toLowerCase();
    const age = Number(stats.last_frame_age_s);
    const hasAge = Number.isFinite(age) && age >= 0;
    const online = !!stats.online;

    if (status === 'disabled') {
        return { label: 'disabled', color: '#9e9e9e', borderColor: 'rgba(158,158,158,0.45)' };
    }

    if (online) {
        return { label: 'online', color: '#00ff88', borderColor: 'rgba(0,255,136,0.45)' };
    }

    if (hasAge && age >= CAMERA_STALL_THRESHOLD_S && age < CAMERA_OFFLINE_THRESHOLD_S) {
        return {
            label: `stalled (${age.toFixed(1)}s)`,
            color: '#ffd166',
            borderColor: 'rgba(255,209,102,0.55)'
        };
    }

    if (hasAge) {
        return {
            label: `offline (${age.toFixed(1)}s)`,
            color: '#ff6b6b',
            borderColor: 'rgba(255,107,107,0.45)'
        };
    }

    return { label: 'offline', color: '#ff6b6b', borderColor: 'rgba(255,107,107,0.45)' };
}

function refreshMainVideoFeed() {
    const camera1Feed = document.getElementById('video-feed-camera1');
    const camera2Feed = document.getElementById('video-feed-camera2');

    if (camera1Feed && cameraEnabledState.camera1 !== false) {
        const streamUrl = `/video_feed/camera1?quality=${webConfig.liveStreamQuality}`;
        if (camera1Feed.src !== streamUrl) {
            camera1Feed.src = streamUrl;
        }
    } else if (camera1Feed) {
        camera1Feed.src = `/api/current_frame/camera1?quality=${webConfig.currentFrameQuality}&ts=${Date.now()}`;
    }
    if (camera2Feed && cameraEnabledState.camera2 !== false) {
        const streamUrl = `/video_feed/camera2?quality=${webConfig.liveStreamQuality}`;
        if (camera2Feed.src !== streamUrl) {
            camera2Feed.src = streamUrl;
        }
    } else if (camera2Feed) {
        camera2Feed.src = `/api/current_frame/camera2?quality=${webConfig.currentFrameQuality}&ts=${Date.now()}`;
    }
}

function startMainVideoFeedPolling() {
    if (mainFeedInterval) {
        clearInterval(mainFeedInterval);
    }

    refreshMainVideoFeed();
    mainFeedInterval = null;
}

function updateSourceToggleBadge(mode) {
    const toggleButton = document.getElementById('source-toggle');
    const modeText = document.getElementById('source-mode-text');
    if (!toggleButton || !modeText) {
        return;
    }

    if (mode === 'dataset') {
        toggleButton.classList.add('dataset-mode');
        modeText.textContent = translations[currentLang]['dataset-mode'] || 'DATASET';
    } else {
        toggleButton.classList.remove('dataset-mode');
        modeText.textContent = translations[currentLang]['live'] || 'LIVE';
    }
}

function initSourceToggle() {
    if (sourceToggleInitialized) {
        return;
    }

    const toggleButton = document.getElementById('source-toggle');
    if (!toggleButton) {
        return;
    }

    updateSourceToggleBadge(currentInputMode);

    toggleButton.addEventListener('click', async function() {
        if (isSwitchingSource) {
            return;
        }

        const nextMode = currentInputMode === 'dataset' ? 'camera' : 'dataset';

        isSwitchingSource = true;
        toggleButton.disabled = true;

        try {
            const response = await fetch('/api/input_source', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mode: nextMode,
                    dataset_path: currentDatasetPath,
                }),
            });

            const result = await response.json();
            if (!response.ok || !result.success) {
                alert(result.message || translations[currentLang]['switch-input-failed'] || 'Failed to switch input source.');
                return;
            }

            currentInputMode = result.mode || nextMode;
            currentDatasetPath = result.dataset_path || currentDatasetPath;
            updateSourceToggleBadge(currentInputMode);
            refreshMainVideoFeed();
            updateStats();
        } catch (error) {
            console.error('VespAI Dashboard: Failed to switch input source:', error);
            alert(translations[currentLang]['switch-input-failed'] || 'Failed to switch input source.');
        } finally {
            toggleButton.disabled = false;
            isSwitchingSource = false;
        }
    });

    sourceToggleInitialized = true;
}

function setCameraToggleVisualState(cameraId, enabled) {
    const toggle = document.getElementById(`${cameraId}-toggle`);
    if (!toggle) {
        return;
    }
    if (toggle.checked !== !!enabled) {
        toggle.checked = !!enabled;
    }
}

async function setCameraEnabled(cameraId, enabled, toggleElement) {
    if (!cameraAvailableState[cameraId]) {
        setCameraToggleVisualState(cameraId, false);
        return;
    }

    if (cameraToggleBusy[cameraId]) {
        return;
    }

    const previousState = cameraEnabledState[cameraId] !== false;
    cameraToggleBusy[cameraId] = true;
    if (toggleElement) {
        toggleElement.disabled = true;
    }

    try {
        const response = await fetch('/api/camera_state', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ camera_id: cameraId, enabled: !!enabled }),
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || `Failed to update ${cameraId}`);
        }

        const serverState = result.camera_enabled || {};
        applyCameraStateFromServer(serverState, result.camera_modes || {});
        refreshMainVideoFeed();
        updateStats();
    } catch (error) {
        console.error(`VespAI Dashboard: Failed to set ${cameraId} enabled state:`, error);
        cameraEnabledState[cameraId] = previousState;
        setCameraToggleVisualState(cameraId, previousState);
    } finally {
        if (toggleElement) {
            toggleElement.disabled = false;
        }
        cameraToggleBusy[cameraId] = false;
    }
}

function initCameraToggles() {
    if (cameraTogglesInitialized) {
        return;
    }

    applyCameraStateFromServer({}, {});

    ['camera1', 'camera2'].forEach((cameraId) => {
        const toggle = document.getElementById(`${cameraId}-toggle`);
        if (!toggle) {
            return;
        }
        toggle.addEventListener('change', function() {
            setCameraEnabled(cameraId, this.checked, this);
        });
    });

    cameraTogglesInitialized = true;
}

function applyPreviewSizing() {
    const previewImage = document.getElementById('source-preview');
    if (!previewImage) {
        return;
    }

    previewImage.style.maxWidth = `${webConfig.webPreviewWidth}px`;
    previewImage.style.maxHeight = `${webConfig.webPreviewHeight}px`;
    previewImage.style.width = `min(100%, ${webConfig.webPreviewWidth}px)`;
}

// Initialize custom cursor (only on desktop)
document.addEventListener('DOMContentLoaded', function() {
    // Initialize language
    translatePage();
    initSourceToggle();
    initCameraToggles();
    initInsightsPanel();
    applyPreviewSizing();
    startMainVideoFeedPolling();
    
    // Add language switch event listeners
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            switchLanguage(lang);
        });
    });
    // Check if this is a mobile/touch device
    const isMobile = window.matchMedia('(pointer: coarse)').matches || window.innerWidth <= 640;
    
    if (isMobile) {
        console.log('VespAI Dashboard: Mobile device detected, skipping custom cursor');
        return;
    }
    
    console.log('VespAI Dashboard: Initializing custom orange neon cursor...');
    
    try {
        // Create cursor element
        cursor = document.createElement('div');
        // Set individual properties for better browser compatibility
        cursor.style.position = 'fixed';
        cursor.style.width = '16px';
        cursor.style.height = '16px';
        cursor.style.backgroundColor = '#ff6600';
        cursor.style.border = '2px solid #ffffff';
        cursor.style.borderRadius = '50%';
        cursor.style.pointerEvents = 'none';
        cursor.style.zIndex = '99999';
        cursor.style.boxShadow = '0 0 15px #ff6600, 0 0 25px #ff6600';
        cursor.style.transform = 'translate(-50%, -50%)';
        cursor.style.opacity = '1';
        document.body.appendChild(cursor);
        console.log('VespAI Dashboard: Custom cursor created and added to page!');
    } catch (error) {
        console.error('VespAI Dashboard: Failed to create cursor:', error);
        // Fallback: just disable default cursor
        document.body.style.cursor = 'none';
    }
    
    // Animate the glow (simplified for better performance)
    setInterval(() => {
        try {
            if (cursor && cursor.style) {
                const intensity = Math.sin(Date.now() * 0.003) * 0.3 + 0.7;
                const glowSize = Math.round(10 + intensity * 10);
                cursor.style.boxShadow = `0 0 ${glowSize}px #ff6600, 0 0 ${glowSize * 2}px rgba(255, 102, 0, 0.6)`;
            }
        } catch (error) {
            console.error('VespAI Dashboard: Animation error:', error);
        }
    }, 100);
});

// Track mouse movement
document.addEventListener('mousemove', function(e) {
    try {
        if (cursor && cursor.style) {
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
        }
    } catch (error) {
        console.error('VespAI Dashboard: Mouse tracking error:', error);
    }
});

// Hide cursor when leaving window
document.addEventListener('mouseleave', function() {
    if (cursor) cursor.style.opacity = '0';
});

// Show cursor when entering window
document.addEventListener('mouseenter', function() {
    if (cursor) cursor.style.opacity = '1';
});

// Track log entries to prevent duplicates
let logMap = new Map();
let lastChartUpdate = 0;
let lastPreviewFrameId = -1;
let latestDetectionPreviewDataUrl = null;
let latestDetectionPreviewFrameId = null;

function updateLastDetectionPreview(frameId) {
    const previewImage = document.getElementById('source-preview');
    if (!previewImage || !frameId || frameId === lastPreviewFrameId) {
        return;
    }

    previewImage.style.display = 'block';
    lastPreviewFrameId = frameId;
    previewImage.src = `/api/detection_frame/${frameId}?quality=${webConfig.currentFrameQuality}&ts=${Date.now()}`;
}

// Update time
function updateTime() {
    try {
        const now = new Date();
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = now.toTimeString().split(' ')[0];
        }
    } catch (error) {
        console.error('VespAI Dashboard: Time update error:', error);
    }
}
setInterval(updateTime, 1000);
updateTime();

// Update log without flickering
function updateLog(logData) {
    try {
        const logContent = document.getElementById('log-content');
        if (!logContent) {
            console.warn('VespAI Dashboard: log-content element not found');
            return;
        }
        const currentIds = new Set();

    // Process each log entry
    logData.forEach((entry, index) => {
        // Validate entry data
        if (!entry || !entry.timestamp || !entry.species) {
            console.warn('VespAI Dashboard: Invalid log entry:', entry);
            return;
        }
        
        const entryId = `${entry.timestamp}-${entry.species}-${entry.frame_id || 'no-frame'}`;
        currentIds.add(entryId);

        // Only add if it's a new entry
        if (!logMap.has(entryId)) {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry new ${entry.species}` + (entry.frame_id ? ' clickable' : '');
            let speciesText = '';
            if (entry.species === 'velutina') {
                speciesText = translations[currentLang]['asian-hornet'] || 'Asian Hornet';
            } else if (entry.species === 'crabro') {
                speciesText = translations[currentLang]['european-hornet'] || 'European Hornet';
            } else if (entry.species === 'bee') {
                speciesText = translations[currentLang]['bee-class'] || 'Bee';
            } else if (entry.species === 'wasp') {
                speciesText = translations[currentLang]['wasp-class'] || 'Unknown';
            } else {
                speciesText = entry.model_label || `class ${entry.class_id ?? 'unknown'}`;
            }
            
            const detectedText = translations[currentLang]['detected'] || 'detected';
            const confidenceText = translations[currentLang]['confidence'] || 'confidence';
            const cameraId = entry.camera_id || 'camera1';
            const cameraAlias = (entry.camera_alias || cameraAliases[cameraId] || cameraId || 'camera1').toString();
            const frameImgHtml = entry.frame_id
                ? `<img class="log-thumb" src="/api/detection_frame/${entry.frame_id}?quality=${webConfig.currentFrameQuality}" alt="Detection ${entry.frame_id}" loading="lazy">`
                : '';
            
            logEntry.innerHTML = `
                <div class="log-main">
                    ${frameImgHtml}
                    <div class="log-details">
                        <div class="log-time"><i class="fas fa-clock"></i> ${entry.timestamp || 'Unknown time'} <span class="log-camera">[${cameraAlias}]</span></div>
                        <div>${speciesText} ${detectedText} (${confidenceText}: ${entry.confidence || 'Unknown'}%)</div>
                    </div>
                </div>
            `;
            logEntry.dataset.id = entryId;
            if (entry.frame_id) {
                logEntry.dataset.frameId = entry.frame_id;
            }

            // Add click handler
            logEntry.addEventListener('click', function() {
                if (entry.frame_id) {
                    showDetectionFrame(entry.frame_id);
                }
            });

            // Add at the top
            logContent.insertBefore(logEntry, logContent.firstChild);
            logMap.set(entryId, logEntry);

            if (entry.frame_id && logContent.firstChild === logEntry) {
                updateLastDetectionPreview(entry.frame_id);
            }

            // Remove 'new' class after animation
            setTimeout(() => {
                logEntry.classList.remove('new');
            }, 500);
        }
    });

    // Remove old entries not in current data
    const allEntries = logContent.querySelectorAll('.log-entry');
    allEntries.forEach((element) => {
        const id = element.dataset.id;
        if (id && !currentIds.has(id)) {
            element.remove();
            logMap.delete(id);
        }
    });

    // Keep only last 20 visible
    while (logContent.children.length > 20) {
        const lastChild = logContent.lastChild;
        const id = lastChild.dataset.id;
        if (id) logMap.delete(id);
        lastChild.remove();
    }
    } catch (error) {
        console.error('VespAI Dashboard: Error updating log:', error);
    }
}

// Smooth value updates
function updateValue(elementId, newValue, suffix = '') {
    try {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`VespAI Dashboard: Element '${elementId}' not found`);
            return;
        }
        
        if (element.textContent !== null && element.textContent !== undefined) {
            const currentValue = element.textContent.replace(suffix, '');
            if (currentValue !== newValue.toString()) {
                element.style.transform = 'scale(1.1)';
                element.textContent = newValue + suffix;
                setTimeout(() => {
                    if (element && element.style) {
                        element.style.transform = 'scale(1)';
                    }
                }, 300);
            }
        } else {
            // Element exists but textContent is null/undefined, just set it
            console.log(`VespAI Dashboard: Setting initial value for '${elementId}': ${newValue}${suffix}`);
            element.textContent = newValue + suffix;
        }
    } catch (error) {
        console.error(`VespAI Dashboard: Error updating element '${elementId}' with value '${newValue}${suffix}':`, error);
    }
}

function updateConfidenceThresholdBadge(value) {
    const badge = document.getElementById('confidence-threshold-badge');
    if (!badge) {
        return;
    }

    const numeric = Number(value);
    const safeValue = Number.isFinite(numeric) ? numeric : 0.5;
    badge.textContent = `CONF ${safeValue.toFixed(2)}`;
}

// Fetch live stats
function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            try {
            // --- PATCH START: Update motion/save LEDs ---
            const motionLed = document.getElementById('motion-led');
            if (motionLed) {
                if (data.enable_motion_detection) {
                    motionLed.style.background = '#00ff88';
                    motionLed.style.boxShadow = '0 0 8px #00ff88, 0 0 16px #00ff88';
                } else {
                    motionLed.style.background = '#444';
                    motionLed.style.boxShadow = 'none';
                }
            }
            const saveLed = document.getElementById('save-led');
            if (saveLed) {
                if (data.save_detections) {
                    saveLed.style.background = '#00ff88';
                    saveLed.style.boxShadow = '0 0 8px #00ff88, 0 0 16px #00ff88';
                } else {
                    saveLed.style.background = '#444';
                    saveLed.style.boxShadow = 'none';
                }
            }
            updateConfidenceThresholdBadge(data.confidence_threshold);
            // --- PATCH END ---
            latestDetectionPreviewDataUrl = data.last_detection_preview || null;
            latestDetectionPreviewFrameId = data.last_detection_preview_frame_id || null;
            // Check system health
            if (data.system_health) {
                if (data.system_health.status === 'warning') {
                    console.warn('System may be frozen - no updates for', data.system_health.time_since_last_frame, 'seconds');
                    document.body.classList.add('system-warning');
                } else {
                    document.body.classList.remove('system-warning');
                }
            }
            // Update counters with animation
            updateValue('frame-count', data.frame_id || 0);
            updateValue('bee-count', data.total_bee || 0);
            updateValue('velutina-count', data.total_velutina || 0);
            updateValue('crabro-count', data.total_crabro || 0);
            updateValue('wasp-count', data.total_wasp || 0);
            updateValue('total-detections', data.total_detections || 0);
            updateValue('sms-count-mini', data.sms_sent || 0);
            
            // Update SMS cost
            if (data.sms_cost !== undefined) {
                const smsCostElement = document.getElementById('sms-cost-mini');
                if (smsCostElement) {
                    smsCostElement.textContent = data.sms_cost.toFixed(2) + '€';
                }
            }

            const beeLastElement = document.getElementById('bee-last');
            if (beeLastElement) beeLastElement.textContent = data.last_bee_time || '-';
            const waspLastElement = document.getElementById('wasp-last');
            if (waspLastElement) waspLastElement.textContent = data.last_wasp_time || '-';
            const velutinaLastElement = document.getElementById('velutina-last');
            if (velutinaLastElement) velutinaLastElement.textContent = data.last_velutina_time || '-';
            const crabroLastElement = document.getElementById('crabro-last');
            if (crabroLastElement) crabroLastElement.textContent = data.last_crabro_time || '-';

            // Update other stats (with translation)
            const fpsElement = document.getElementById('fps');
            if (fpsElement) {
                const fpsText = translations[currentLang]['fps-suffix'] || 'FPS';
                fpsElement.textContent = (data.fps || 0).toFixed(1) + ' ' + fpsText;
            }

            const perCamera = data.per_camera || {};
            applyCameraAliases(data.camera_aliases || {});
            const cameraEnabled = data.camera_enabled || {};
            const cameraModes = data.camera_modes || {};
            applyCameraStateFromServer(cameraEnabled, cameraModes);

            const camera1Source = (perCamera.camera1 && perCamera.camera1.current_frame_source) || '';
            const camera2Source = (perCamera.camera2 && perCamera.camera2.current_frame_source) || '';

            const camera1FpsEl = document.getElementById('camera1-fps');
            const camera2FpsEl = document.getElementById('camera2-fps');
            const camera1SourceEl = document.getElementById('camera1-source');
            const camera2SourceEl = document.getElementById('camera2-source');
            const camera1HealthBadge = document.getElementById('camera1-health-badge');
            const camera2HealthBadge = document.getElementById('camera2-health-badge');
            const camera1AgeEl = document.getElementById('camera1-age');
            const camera2AgeEl = document.getElementById('camera2-age');

            const camera1Fps = (perCamera.camera1 && perCamera.camera1.fps) || 0;
            const camera2Fps = (perCamera.camera2 && perCamera.camera2.fps) || 0;
            const camera1Stats = perCamera.camera1 || {};
            const camera2Stats = perCamera.camera2 || {};

            if (camera1FpsEl) camera1FpsEl.textContent = Number(camera1Fps).toFixed(1);
            if (camera2FpsEl) camera2FpsEl.textContent = Number(camera2Fps).toFixed(1);
            if (camera1SourceEl) camera1SourceEl.textContent = camera1Source || (translations[currentLang]['waiting'] || 'waiting...');
            if (camera2SourceEl) camera2SourceEl.textContent = camera2Source || (translations[currentLang]['waiting'] || 'waiting...');
            if (camera1AgeEl) camera1AgeEl.textContent = formatFrameAge(camera1Stats.last_frame_age_s);
            if (camera2AgeEl) camera2AgeEl.textContent = formatFrameAge(camera2Stats.last_frame_age_s);

            if (camera1HealthBadge) {
                const camera1Health = deriveCameraHealth(camera1Stats);
                camera1HealthBadge.textContent = camera1Health.label;
                camera1HealthBadge.style.color = camera1Health.color;
                camera1HealthBadge.style.borderColor = camera1Health.borderColor;
            }
            if (camera2HealthBadge) {
                const camera2Health = deriveCameraHealth(camera2Stats);
                camera2HealthBadge.textContent = camera2Health.label;
                camera2HealthBadge.style.color = camera2Health.color;
                camera2HealthBadge.style.borderColor = camera2Health.borderColor;
            }

            if (!isSwitchingSource && data.input_mode) {
                currentInputMode = data.input_mode;
                currentDatasetPath = data.dataset_path || currentDatasetPath;
                updateSourceToggleBadge(currentInputMode);
                if (lastRenderedInputMode !== currentInputMode) {
                    refreshMainVideoFeed();
                    lastRenderedInputMode = currentInputMode;
                }
            }

            // Update system info with safety checks
            if (data.cpu_temp !== undefined) {
                const cpuTempElement = document.getElementById('cpu-temp');
                if (cpuTempElement) cpuTempElement.textContent = Math.round(data.cpu_temp) + '°C';
                const inferenceCpuTempElement = document.getElementById('inference-cpu-temp');
                if (inferenceCpuTempElement) inferenceCpuTempElement.textContent = Math.round(data.cpu_temp) + '°C';
            }
            const inferenceAvgElement = document.getElementById('inference-avg');
            if (inferenceAvgElement) inferenceAvgElement.textContent = `${data.inference_avg_ms || 0} ms`;
            const inferenceMinElement = document.getElementById('inference-min');
            if (inferenceMinElement) inferenceMinElement.textContent = `${data.inference_min_ms || 0} ms`;
            const inferenceMaxElement = document.getElementById('inference-max');
            if (inferenceMaxElement) inferenceMaxElement.textContent = `${data.inference_max_ms || 0} ms`;
            if (data.cpu_usage !== undefined) {
                const cpuUsageElement = document.getElementById('cpu-usage');
                if (cpuUsageElement) cpuUsageElement.textContent = data.cpu_usage + '%';
            }
            if (data.ram_usage !== undefined) {
                const ramUsageElement = document.getElementById('ram-usage');
                if (ramUsageElement) ramUsageElement.textContent = data.ram_usage + '%';
            }
            if (data.uptime !== undefined) {
                const uptimeElement = document.getElementById('uptime-sys');
                if (uptimeElement) uptimeElement.textContent = data.uptime;
            }

            // Update log without flickering
            if (data.detection_log) {
                updateLog(data.detection_log);
            }

            const previewLabel = document.getElementById('preview-label');
            if (previewLabel) {
                previewLabel.textContent = translations[currentLang]['last-detection-preview'] || 'Last Detection Image';
            }

            const previewImage = document.getElementById('source-preview');
            const topLogEntry = document.querySelector('#log-content .log-entry.clickable');
            const previewFrameId = topLogEntry && topLogEntry.dataset ? topLogEntry.dataset.frameId : null;

            if (previewImage) {
                if (previewFrameId && previewFrameId !== lastPreviewFrameId) {
                    previewImage.style.display = 'block';
                    updateLastDetectionPreview(previewFrameId);
                } else if (!previewFrameId) {
                    previewImage.style.display = 'none';
                    previewImage.removeAttribute('src');
                    lastPreviewFrameId = null;
                }
            }

            // Update hourly chart - use different data based on screen size
            if ((data.hourly_data_24h || data.hourly_data_4h) && (Date.now() - lastChartUpdate > 10000)) {
                lastChartUpdate = Date.now();
                const chart = document.getElementById('hourly-chart');
                chart.innerHTML = '';
                
                // Choose dataset based on screen size
                const isMobile = window.innerWidth <= 768;
                const chartData = isMobile ? data.hourly_data_4h : data.hourly_data_24h;
                
                if (!chartData) return;
                
                // Update chart title based on view and language
                const titleElement = document.querySelector('.chart-title-text');
                if (titleElement) {
                    const titleKey = isMobile ? 'chart-title-4h' : 'chart-title-24h';
                    titleElement.textContent = translations[currentLang][titleKey] || 
                        (isMobile ? 'Detections per 4-Hour Block (Last 24h)' : 'Detections per Hour (Last 24h)');
                }
                
                const maxVal = Math.max(...chartData.map(h => h.total), 1);
                
                chartData.forEach(hour => {
                    const bar = document.createElement('div');
                    bar.className = 'time-bar';
                    const height = Math.max(((hour.total / maxVal) * 100), 2);
                    bar.style.height = height + '%';

                    if (hour.velutina > 0 && hour.crabro > 0) {
                        bar.style.background = 'linear-gradient(180deg, var(--danger) 0%, var(--honey) 100%)';
                    } else if (hour.velutina > 0) {
                        bar.style.background = 'linear-gradient(180deg, var(--danger) 0%, #ff0066 100%)';
                    } else if (hour.crabro > 0) {
                        bar.style.background = 'linear-gradient(180deg, var(--honey) 0%, var(--honey-dark) 100%)';
                    } else {
                        bar.style.background = 'rgba(255,255,255,0.1)';
                    }

                    bar.innerHTML = `<span class="time-bar-label">${hour.hour}</span>`;
                    bar.title = `${hour.hour} - Velutina: ${hour.velutina}, Crabro: ${hour.crabro}`;
                    chart.appendChild(bar);
                });
            }

            const inferenceChart = document.getElementById('inference-chart');
            const inferenceAxis = document.getElementById('inference-y-axis');
            if (inferenceChart && inferenceAxis && Array.isArray(data.inference_timing_recent)) {
                inferenceChart.innerHTML = '';
                inferenceAxis.innerHTML = '';
                const recentTimings = data.inference_timing_recent.slice(-20);
                const maxMs = Math.max(...recentTimings.map(item => item.duration_ms || 0), 1);
                const axisTicks = [maxMs, maxMs / 2, 0];

                axisTicks.forEach(value => {
                    const tick = document.createElement('div');
                    tick.className = 'inference-y-tick';
                    tick.textContent = `${Math.round(value)} ms`;
                    inferenceAxis.appendChild(tick);
                });

                recentTimings.forEach(item => {
                    const bar = document.createElement('div');
                    bar.className = 'inference-bar';
                    const height = Math.max(((item.duration_ms || 0) / maxMs) * 140, 6);
                    bar.style.height = `${height}px`;
                    bar.title = `${item.label}: ${item.duration_ms} ms`;
                    bar.innerHTML = `<span class="inference-bar-label">${item.frame_id}</span>`;
                    inferenceChart.appendChild(bar);
                });
            }

            if (insightsOpen) {
                refreshInsights();
            }
            } catch (error) {
                console.error('VespAI Dashboard: Error processing stats data:', error);
            }
        })
        .catch(error => {
            console.error('VespAI Dashboard: Error fetching stats:', error);
        });
}

// Fullscreen function
function toggleFullscreen() {
    const video = document.getElementById('video-feed-camera1') || document.getElementById('video-feed-camera2');
    if (!video) {
        return;
    }
    if (!document.fullscreenElement) {
        video.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable fullscreen: ${err.message}`);
        });
    } else {
        document.exitFullscreen();
    }
}

// Show detection frame in new tab/window
function showDetectionFrame(frameId) {
    const frameUrl = `/frame/${frameId}`;
    window.open(frameUrl, '_blank');
}

// Update stats on a moderate cadence for Raspberry Pi performance
let statsInterval = setInterval(updateStats, 5000);
updateStats();

// Prevent multiple intervals from running
window.addEventListener('beforeunload', function() {
    if (statsInterval) {
        clearInterval(statsInterval);
    }
    if (mainFeedInterval) {
        clearInterval(mainFeedInterval);
    }
});