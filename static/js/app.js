/**
 * AutoClip Studio Ultra Pro — Pure JavaScript Single Page Application
 * Renders dynamically into <div id="app"></div> with zero static HTML bloat.
 * Multi-User Isolated Concurrency & Enterprise Resiliency.
 */

import { renderNavbar } from './components/Navbar.js';
import { renderHeroInput } from './components/HeroInput.js';
import { renderPipelineControls } from './components/PipelineControls.js';
import { renderLanguageModePicker } from './components/LanguageModePicker.js';
import { renderSubtitleStylePicker } from './components/SubtitleStylePicker.js';
import { renderActiveJobMonitor } from './components/ActiveJobMonitor.js';
import { renderBatchQueuePanel } from './components/BatchQueuePanel.js';
import { renderGalleryView } from './components/GalleryView.js';
import { renderBiomimeticModal } from './components/BiomimeticModal.js';

class AutoClipApp {
  constructor() {
    // 1. Session Isolation: Retrieve or generate unique client session ID with safe fallback
    let sid = null;
    try {
      sid = localStorage.getItem('autoclip_session_id');
      if (!sid) {
        sid = 'user_' + Math.random().toString(36).substring(2, 10);
        localStorage.setItem('autoclip_session_id', sid);
      }
    } catch (e) {
      console.warn('LocalStorage unavailable or restricted, using memory session:', e);
      sid = 'user_' + Math.random().toString(36).substring(2, 10);
    }

    this.state = {
      sessionId: sid,
      activeInputTab: 'single', // 'single' | 'batch'
      youtubeUrl: '',
      batchUrlsText: '',
      batchUrls: [],
      inspectData: null,
      localVideoPath: null,

      genre: 'Podcast',
      clippingMode: 'smart_highlights',
      numClips: 3,
      chunkSizeSec: '30',
      downloadResolution: '720p',

      subLanguageMode: 'original', // 'original' | 'en_translate'
      subPreset: 'aujle_tere_te',
      subPosition: 'bottom',
      customWordsPerLine: 2,
      highlightWords: true,

      // Custom Subtitle Colors & Geometry Dimensions
      customHighlightColor: '#18C5F5',
      customPrimaryColor: '#FFFFFF',
      customGlowColor: '#0088FF',
      customFontSize: 65,
      customOutlineWidth: 5,
      customShadow: 3,
      customUppercase: true,

      activeJob: null,
      queueSummary: { waiting_jobs: [] },
      gallery: [],
      systemMemory: {},
      hardwareEncoder: {},
      routeStatus: [],
      showTelemetryModal: false,
    };

    this.pollInterval = null;
    this.sseSource = null;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // INITIALIZATION
  // ──────────────────────────────────────────────────────────────────────────
  init() {
    this.render();
    this.attachEventListeners();
    this.loadInitialData();

    // Start background status polling (every 2.5 seconds)
    this.pollInterval = setInterval(() => this.pollStatus(), 2500);
  }

  // ──────────────────────────────────────────────────────────────────────────
  // RENDER COMPLETE UI DIRECTLY INTO #app
  // ──────────────────────────────────────────────────────────────────────────
  render() {
    const root = document.getElementById('app');
    if (!root) return;

    root.innerHTML = `
      <div class="studio-wrapper">
        ${renderNavbar(this.state)}

        <main class="studio-main-flow">
          ${renderHeroInput(this.state)}
          ${renderPipelineControls(this.state)}
          ${renderLanguageModePicker(this.state)}
          ${renderSubtitleStylePicker(this.state)}
          ${renderActiveJobMonitor(this.state)}
          ${renderBatchQueuePanel(this.state)}
          ${renderGalleryView(this.state)}
        </main>
      </div>

      ${renderBiomimeticModal(this.state)}
    `;

    window.__appMounted = true;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // EVENT ATTACHMENTS (EVENT DELEGATION FOR DYNAMIC JS DOM)
  // ──────────────────────────────────────────────────────────────────────────
  attachEventListeners() {
    document.addEventListener('click', (e) => this.handleClick(e));
    document.addEventListener('input', (e) => this.handleInput(e));
    document.addEventListener('change', (e) => this.handleChange(e));

    // Drag and Drop support
    window.addEventListener('dragover', (e) => e.preventDefault());
    window.addEventListener('drop', (e) => e.preventDefault());
  }

  handleClick(e) {
    const target = e.target;

    // 1. Navigation / Modal Actions
    if (target.closest('#btnOpenTelemetry')) {
      this.state.showTelemetryModal = true;
      this.render();
      return;
    }
    if (target.closest('#btnCloseTelemetry') || target.closest('#btnDismissTelemetry') || target.id === 'telemetryBackdrop') {
      this.state.showTelemetryModal = false;
      this.render();
      return;
    }
    if (target.closest('#btnPurgeCache')) {
      this.purgeCache();
      return;
    }
    if (target.closest('#btnScrollGallery')) {
      const g = document.getElementById('gallerySection');
      if (g) g.scrollIntoView({ behavior: 'smooth' });
      return;
    }

    // 2. Input Mode Tabs
    if (target.closest('#tabSingleVideo')) {
      this.state.activeInputTab = 'single';
      this.render();
      return;
    }
    if (target.closest('#tabBatchQueue')) {
      this.state.activeInputTab = 'batch';
      this.render();
      return;
    }

    // 3. Inspect Video Trigger
    if (target.closest('#btnInspectVideo')) {
      this.inspectVideo();
      return;
    }
    if (target.closest('#btnDismissInspect')) {
      this.state.inspectData = null;
      this.render();
      return;
    }

    // 4. File Dropzone Click
    if (target.closest('#dropzoneClickable')) {
      const fi = document.getElementById('localFileInput');
      if (fi) fi.click();
      return;
    }

    // 5. Genre Selection
    const genreCard = target.closest('.genre-card');
    if (genreCard) {
      this.state.genre = genreCard.dataset.genre;
      this.render();
      return;
    }

    // Duration Pills (Full Video Boxer) - Checked before parent modeCard
    const durPill = target.closest('.duration-pill');
    if (durPill) {
      this.state.chunkSizeSec = durPill.dataset.chunk;
      this.render();
      return;
    }

    // 6. Clipping Mode
    const modeCard = target.closest('.mode-card');
    if (modeCard) {
      this.state.clippingMode = modeCard.dataset.mode;
      this.render();
      return;
    }

    // 7. Language Mode
    const langCard = target.closest('.lang-card');
    if (langCard) {
      this.state.subLanguageMode = langCard.dataset.langmode;
      this.render();
      return;
    }

    // 8. Subtitle Preset
    const presetCard = target.closest('.preset-card');
    if (presetCard) {
      this.state.subPreset = presetCard.dataset.preset;
      if (presetCard.dataset.color) {
        this.state.customHighlightColor = presetCard.dataset.color;
      }
      if (presetCard.dataset.glow) {
        this.state.customGlowColor = presetCard.dataset.glow;
      }
      this.render();
      return;
    }

    // Color Swatches
    const swatchBtn = target.closest('.color-swatch-btn');
    if (swatchBtn) {
      const type = swatchBtn.dataset.target;
      const color = swatchBtn.dataset.color;
      if (type === 'highlight') {
        this.state.customHighlightColor = color;
      } else if (type === 'primary') {
        this.state.customPrimaryColor = color;
      } else if (type === 'glow') {
        this.state.customGlowColor = color;
      }
      this.render();
      return;
    }

    // Dimension Quick Preset Pills (Font Size & Outline Width)
    const dimPill = target.closest('.dim-pill');
    if (dimPill) {
      const type = dimPill.dataset.type;
      const val = parseInt(dimPill.dataset.val, 10);
      if (type === 'size') {
        this.state.customFontSize = val;
      } else if (type === 'outline') {
        this.state.customOutlineWidth = val;
      }
      this.render();
      return;
    }

    // Text Casing Toggles
    if (target.closest('#btnCaseUpper')) {
      this.state.customUppercase = true;
      this.render();
      return;
    }
    if (target.closest('#btnCaseNormal')) {
      this.state.customUppercase = false;
      this.render();
      return;
    }

    // Subtitle Position
    const posPill = target.closest('.pos-pill');
    if (posPill) {
      this.state.subPosition = posPill.dataset.pos;
      this.render();
      return;
    }

    // 9. Primary Generation Trigger
    if (target.closest('#btnGenerateShorts')) {
      this.startGeneration();
      return;
    }

    // 10. Batch Queue Submit
    if (target.closest('#btnAddBatchQueue')) {
      this.submitBatchQueue();
      return;
    }

    // 11. Cancel Active Job
    const btnCancel = target.closest('#btnCancelActiveJob');
    if (btnCancel) {
      this.cancelJob(btnCancel.dataset.jobid);
      return;
    }

    // Cancel Queued Job
    const btnCancelQ = target.closest('.btnCancelQueued');
    if (btnCancelQ) {
      this.cancelJob(btnCancelQ.dataset.jobid);
      return;
    }

    // Clear All Queue
    if (target.closest('#btnClearAllQueue')) {
      this.clearAllQueue();
      return;
    }

    // 12. Refresh Gallery
    if (target.closest('#btnRefreshGallery')) {
      this.loadGallery();
      return;
    }

    // Delete Short
    const btnDel = target.closest('.btnDeleteShort');
    if (btnDel) {
      this.deleteShort(btnDel.dataset.filename);
      return;
    }

    // Copy Logs
    if (target.closest('#btnCopyLogs')) {
      const lines = (this.state.activeJob?.logs || []).join('\n');
      navigator.clipboard.writeText(lines).then(() => alert('Logs copied to clipboard!'));
      return;
    }
  }

  handleInput(e) {
    if (e.target.id === 'inputYoutubeUrl') {
      this.state.youtubeUrl = e.target.value.trim();
    } else if (e.target.id === 'textareaBatchUrls') {
      this.state.batchUrlsText = e.target.value;
      this.state.batchUrls = e.target.value.split('\n').map(u => u.trim()).filter(Boolean);
    } else if (e.target.id === 'inputCustomHighlight') {
      this.state.customHighlightColor = e.target.value;
      const lbl = document.getElementById('lblHighlightHex');
      if (lbl) lbl.textContent = e.target.value;
      const prev = document.getElementById('liveWordHighlight');
      if (prev) {
        prev.style.color = e.target.value;
        prev.style.textShadow = `0 0 14px ${this.state.customGlowColor}, 0 0 4px #000, 0 0 2px #000`;
      }
    } else if (e.target.id === 'inputCustomPrimary') {
      this.state.customPrimaryColor = e.target.value;
      const lbl = document.getElementById('lblPrimaryHex');
      if (lbl) lbl.textContent = e.target.value;
      const prev = document.getElementById('liveWordPrimary');
      if (prev) prev.style.color = e.target.value;
    } else if (e.target.id === 'inputCustomGlow') {
      this.state.customGlowColor = e.target.value;
      const lbl = document.getElementById('lblGlowHex');
      if (lbl) lbl.textContent = e.target.value;
      this.updateLivePreview();
    } else if (e.target.id === 'inputCustomFontSize') {
      const val = parseInt(e.target.value, 10);
      this.state.customFontSize = val;
      const lbl = document.getElementById('lblFontSizeVal');
      if (lbl) lbl.textContent = val + 'px';
      this.updateLivePreview();
    } else if (e.target.id === 'inputCustomOutlineWidth') {
      const val = parseInt(e.target.value, 10);
      this.state.customOutlineWidth = val;
      const lbl = document.getElementById('lblOutlineWidthVal');
      if (lbl) lbl.textContent = val + 'px';
      this.updateLivePreview();
    } else if (e.target.id === 'inputCustomShadow') {
      const val = parseInt(e.target.value, 10);
      this.state.customShadow = val;
      const lbl = document.getElementById('lblShadowVal');
      if (lbl) lbl.textContent = val + 'px';
      this.updateLivePreview();
    }
  }

  updateLivePreview() {
    const hi = document.getElementById('liveWordHighlight');
    const pri = document.getElementById('liveWordPrimary');
    const fSize = Math.round((this.state.customFontSize || 65) * 0.35);
    const stroke = Math.max(0, (this.state.customOutlineWidth !== undefined ? this.state.customOutlineWidth : 5) * 0.22);
    const shadow = (this.state.customShadow !== undefined ? this.state.customShadow : 3) * 4;
    const casing = (this.state.customUppercase !== false) ? 'uppercase' : 'none';

    if (hi) {
      hi.style.fontSize = fSize + 'px';
      hi.style.webkitTextStroke = stroke + 'px #000';
      hi.style.textTransform = casing;
      hi.style.color = this.state.customHighlightColor;
      hi.style.textShadow = `0 0 ${shadow}px ${this.state.customGlowColor}, 0 0 4px #000, 0 0 2px #000`;
    }
    if (pri) {
      pri.style.fontSize = fSize + 'px';
      pri.style.webkitTextStroke = stroke + 'px #000';
      pri.style.textTransform = casing;
      pri.style.color = this.state.customPrimaryColor;
      pri.style.textShadow = `0 0 4px #000, 0 0 2px #000`;
    }
  }

  handleChange(e) {
    if (e.target.id === 'selectNumClips') {
      this.state.numClips = parseInt(e.target.value, 10);
    } else if (e.target.id === 'selectWordsPerLine') {
      this.state.customWordsPerLine = parseInt(e.target.value, 10);
    } else if (e.target.id === 'checkWordPop') {
      this.state.highlightWords = e.target.checked;
    } else if (e.target.id === 'localFileInput') {
      const file = e.target.files[0];
      if (file) this.uploadLocalFile(file);
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // API INTEGRATIONS
  // ──────────────────────────────────────────────────────────────────────────
  async loadInitialData() {
    await Promise.all([
      this.fetchSystemStatus(),
      this.pollQueue(),
      this.loadGallery(),
    ]);
  }

  async fetchSystemStatus() {
    try {
      const res = await fetch('/api/system_status', {
        headers: { 'X-Session-ID': this.state.sessionId }
      });
      if (res.ok) {
        const data = await res.json();
        this.state.systemMemory = data.system_memory || {};
        this.state.hardwareEncoder = data.hardware_encoder || {};
        this.state.routeStatus = data.routes || [];
        this.render();
      }
    } catch (e) {
      console.warn('System status fetch failed:', e);
    }
  }

  async inspectVideo() {
    const inputVal = document.getElementById('inputYoutubeUrl')?.value?.trim();
    if (inputVal) this.state.youtubeUrl = inputVal;
    const url = this.state.youtubeUrl;
    if (!url) {
      alert('Please enter a YouTube URL first.');
      return;
    }

    const spinner = document.getElementById('inspectSpinner');
    if (spinner) spinner.style.display = 'inline-block';

    try {
      const res = await fetch('/api/inspect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.state.sessionId,
        },
        body: JSON.stringify({ youtube_url: url })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.state.inspectData = data.info;
        this.render();
      } else {
        alert('Could not inspect video: ' + (data.message || 'Unknown error'));
      }
    } catch (e) {
      alert('Network error inspecting video: ' + e.message);
    } finally {
      if (spinner) spinner.style.display = 'none';
    }
  }

  async uploadLocalFile(file) {
    const formData = new FormData();
    formData.append('video', file);

    const dropzoneText = document.querySelector('.dropzone-text');
    if (dropzoneText) dropzoneText.innerHTML = `<strong>Uploading ${file.name}...</strong>`;

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'X-Session-ID': this.state.sessionId },
        body: formData,
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.state.localVideoPath = data.file_path;
        this.state.inspectData = data.info;
        this.render();
      } else {
        alert('Upload failed: ' + data.message);
      }
    } catch (e) {
      alert('Upload error: ' + e.message);
    }
  }

  async startGeneration() {
    const inputVal = document.getElementById('inputYoutubeUrl')?.value?.trim();
    if (inputVal) this.state.youtubeUrl = inputVal;

    const params = {
      session_id: this.state.sessionId,
      genre: this.state.genre,
      clipping_mode: this.state.clippingMode,
      num_clips: this.state.numClips,
      chunk_size_sec: this.state.chunkSizeSec,
      download_resolution: this.state.downloadResolution,
      sub_language_mode: this.state.subLanguageMode,
      sub_preset: this.state.subPreset,
      sub_position: this.state.subPosition,
      custom_words_per_line: this.state.customWordsPerLine,
      highlight_words: this.state.highlightWords,
      custom_highlight_color: this.state.customHighlightColor,
      custom_primary_color: this.state.customPrimaryColor,
      custom_glow_color: this.state.customGlowColor,
      custom_sub_size: this.state.customFontSize,
      custom_outline_width: this.state.customOutlineWidth,
      custom_shadow: this.state.customShadow,
      custom_uppercase: this.state.customUppercase,
    };

    if (this.state.localVideoPath) {
      params.local_video_path = this.state.localVideoPath;
    } else if (this.state.youtubeUrl) {
      params.youtube_url = this.state.youtubeUrl;
    } else {
      alert('Please provide a YouTube URL or upload a local video first.');
      return;
    }

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.state.sessionId,
        },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.state.activeJob = {
          job_id: data.job_id,
          status: 'running',
          progress: 5,
          current_step: 'Starting pipeline execution...',
          logs: ['[00:00:00] Job submitted to multi-user executor...'],
        };
        this.render();
        this.connectSseLogs(data.job_id);

        const m = document.getElementById('monitorSection');
        if (m) m.scrollIntoView({ behavior: 'smooth' });
      } else {
        alert('Generation failed to start: ' + data.message);
      }
    } catch (e) {
      alert('Error initiating generation: ' + e.message);
    }
  }

  async submitBatchQueue() {
    const urls = this.state.batchUrls;
    if (!urls || urls.length === 0) {
      alert('Please paste at least one YouTube URL in the batch area.');
      return;
    }

    const payload = {
      session_id: this.state.sessionId,
      urls: urls,
      genre: this.state.genre,
      clipping_mode: this.state.clippingMode,
      num_clips: this.state.numClips,
      chunk_size_sec: this.state.chunkSizeSec,
      sub_language_mode: this.state.subLanguageMode,
      sub_preset: this.state.subPreset,
      sub_position: this.state.subPosition,
      custom_highlight_color: this.state.customHighlightColor,
      custom_primary_color: this.state.customPrimaryColor,
      custom_glow_color: this.state.customGlowColor,
      custom_sub_size: this.state.customFontSize,
      custom_outline_width: this.state.customOutlineWidth,
      custom_shadow: this.state.customShadow,
      custom_uppercase: this.state.customUppercase,
    };

    try {
      const res = await fetch('/api/batch_generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.state.sessionId,
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`Queued ${data.queued_count} videos for processing!`);
        this.state.batchUrlsText = '';
        this.state.batchUrls = [];
        this.pollQueue();
      }
    } catch (e) {
      alert('Error submitting batch: ' + e.message);
    }
  }

  connectSseLogs(jobId) {
    if (this.sseSource) {
      this.sseSource.close();
    }

    this.sseSource = new EventSource(`/api/stream_logs/${jobId}`);
    this.sseSource.onmessage = (event) => {
      try {
        const item = JSON.parse(event.data);
        if (item.log) {
          if (!this.state.activeJob) {
            this.state.activeJob = { job_id: jobId, logs: [] };
          }
          if (!this.state.activeJob.logs) this.state.activeJob.logs = [];
          this.state.activeJob.logs.push(item.log);
          this.updateTerminalDom(item.log);
        }
        if (item.status) {
          this.state.activeJob.status = item.status;
        }
        if (item.progress !== undefined) {
          this.state.activeJob.progress = item.progress;
          this.updateProgressBarDom(item.progress, item.current_step);
        }
        if (item.status === 'completed' || item.status === 'failed') {
          this.sseSource.close();
          this.loadGallery();
        }
      } catch (err) {
        if (this.state.activeJob?.logs) {
          this.state.activeJob.logs.push(event.data);
          this.updateTerminalDom(event.data);
        }
      }
    };

    this.sseSource.onerror = () => {
      if (this.sseSource) this.sseSource.close();
    };
  }

  updateTerminalDom(line) {
    const el = document.getElementById('liveTerminalOutput');
    if (el) {
      const div = document.createElement('div');
      div.className = 'log-line ' + (line.includes('❌') ? 'log-err' : line.includes('✅') ? 'log-ok' : '');
      div.textContent = line;
      el.appendChild(div);
      el.scrollTop = el.scrollHeight;
    }
  }

  updateProgressBarDom(pct, step) {
    const fill = document.querySelector('.progress-bar-fill');
    const label = document.querySelector('.progress-percent');
    const stepEl = document.querySelector('.current-step-label');
    if (fill) fill.style.width = pct + '%';
    if (label) label.textContent = pct + '%';
    if (stepEl && step) stepEl.textContent = step;
  }

  async pollStatus() {
    await Promise.all([
      this.pollActiveJob(),
      this.pollQueue(),
    ]);
  }

  async pollActiveJob() {
    if (!this.state.activeJob?.job_id) return;
    try {
      const res = await fetch(`/api/job_status/${this.state.activeJob.job_id}`);
      if (res.ok) {
        const job = await res.json();
        this.state.activeJob = job;
        if (job.status === 'completed' || job.status === 'failed') {
          this.render();
          this.loadGallery();
        }
      }
    } catch (e) {}
  }

  async pollQueue() {
    try {
      const res = await fetch('/api/queue_status', {
        headers: { 'X-Session-ID': this.state.sessionId }
      });
      if (res.ok) {
        const data = await res.json();
        this.state.queueSummary = data;
        const qSection = document.getElementById('queueSection');
        if (qSection || (data.waiting_jobs && data.waiting_jobs.length > 0)) {
          const container = document.querySelector('.queue-list');
          if (container) {
            container.innerHTML = (data.waiting_jobs || []).map(item => `
              <div class="queue-item">
                <div class="queue-position">#${item.position}</div>
                <div class="queue-details">
                  <div class="queue-title">${item.title}</div>
                  <div class="queue-tags">
                    <span class="tag-pill">${item.genre}</span>
                    <span class="tag-pill">${item.clipping_mode}</span>
                    <span class="tag-pill tag-status">${item.status}</span>
                  </div>
                </div>
                <div class="queue-actions">
                  <button class="studio-btn studio-btn-ghost btn-sm text-danger btnCancelQueued" data-jobid="${item.job_id}">
                    Remove
                  </button>
                </div>
              </div>
            `).join('');
          }
        }
      }
    } catch (e) {}
  }

  async loadGallery() {
    try {
      const res = await fetch('/api/gallery');
      if (res.ok) {
        const data = await res.json();
        this.state.gallery = data.shorts || [];
        const galleryDom = document.getElementById('gallerySection');
        if (galleryDom) {
          galleryDom.outerHTML = renderGalleryView(this.state);
        }
      }
    } catch (e) {}
  }

  async cancelJob(jobId) {
    if (!confirm('Cancel this job?')) return;
    try {
      await fetch(`/api/cancel_job/${jobId}`, { method: 'POST' });
      this.pollQueue();
      if (this.state.activeJob?.job_id === jobId) {
        this.state.activeJob.status = 'cancelled';
        this.render();
      }
    } catch (e) {}
  }

  async clearAllQueue() {
    if (!confirm('Clear all pending jobs in queue?')) return;
    try {
      await fetch('/api/clear_queue', { method: 'POST' });
      this.pollQueue();
    } catch (e) {}
  }

  async deleteShort(filename) {
    if (!confirm('Delete this short permanently from SSD?')) return;
    try {
      await fetch(`/api/delete_short/${filename}`, { method: 'POST' });
      this.loadGallery();
    } catch (e) {}
  }

  async purgeCache() {
    try {
      const res = await fetch('/api/purge_cache', { method: 'POST' });
      const data = await res.json();
      alert(`SSD Cache Cleaned: Freed ${data.freed_mb} MB (${data.deleted_files} files deleted).`);
      this.fetchSystemStatus();
    } catch (e) {
      alert('Error purging cache: ' + e.message);
    }
  }
}

// Robust boot sequence handling both pre-loaded and deferred execution
function bootAutoClip() {
  try {
    if (!window.studioApp) {
      window.studioApp = new AutoClipApp();
      window.studioApp.init();
    }
  } catch (err) {
    console.error('Fatal AutoClip Studio initialization error:', err);
    const root = document.getElementById('app');
    if (root) {
      root.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0b0c10;color:#f0f2f5;font-family:sans-serif;padding:20px;">
          <div style="max-width:540px;background:#14161f;border:1px solid rgba(239,68,68,0.5);border-radius:12px;padding:28px;box-shadow:0 12px 32px rgba(0,0,0,0.6);">
            <h3 style="color:#ef4444;margin:0 0 10px;font-size:18px;">⚠️ Studio Startup Exception</h3>
            <p style="color:#cbd5e1;font-size:13px;line-height:1.6;margin:0 0 16px;">${err.message || 'An error occurred during startup.'}</p>
            <button onclick="location.reload(true)" style="background:#18c5f5;color:#0b0c10;border:none;padding:10px 22px;border-radius:6px;font-weight:700;font-size:13px;cursor:pointer;">Force Hard Reload</button>
          </div>
        </div>
      `;
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootAutoClip);
} else {
  // Document is already interactive or complete
  bootAutoClip();
}
