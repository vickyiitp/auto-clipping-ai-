/**
 * Hero Input Component
 * Supports Single Video Ingestion (URL or Upload) & Multi-URL Batch Studio Queue.
 */

export function renderHeroInput(state) {
  const isBatch = (state.activeInputTab === 'batch');
  const insp = state.inspectData;

  return `
    <div class="studio-card hero-input-card">
      <!-- Input Mode Switcher Tabs -->
      <div class="input-tabs-header">
        <button class="input-tab ${!isBatch ? 'active' : ''}" data-tab="single" id="tabSingleVideo">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon></svg>
          Single Video / File
        </button>
        <button class="input-tab ${isBatch ? 'active' : ''}" data-tab="batch" id="tabBatchQueue">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
          Batch Studio Queue (${state.batchUrls ? state.batchUrls.length : 0})
        </button>
      </div>

      <div class="input-tab-content">
        ${!isBatch ? `
          <!-- SINGLE VIDEO INPUT -->
          <div class="single-input-grid">
            <div class="url-input-wrapper">
              <div class="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              </div>
              <input type="text" id="inputYoutubeUrl" class="studio-input" placeholder="Paste YouTube Video URL (e.g., https://youtu.be/...)" value="${state.youtubeUrl || ''}" autocomplete="off">
              <button class="studio-btn studio-btn-primary" id="btnInspectVideo">
                <span class="btn-spinner" id="inspectSpinner" style="display:none;"></span>
                Inspect Video
              </button>
            </div>

            <div class="or-divider"><span>OR UPLOAD LOCAL VIDEO</span></div>

            <!-- Drag & Drop File Zone -->
            <div class="dropzone" id="dropzoneContainer">
              <input type="file" id="localFileInput" accept="video/mp4,video/mkv,video/webm,video/mov" style="display:none;">
              <div class="dropzone-inner" id="dropzoneClickable">
                <div class="dropzone-icon">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                </div>
                <div class="dropzone-text">
                  <strong>Click to browse</strong> or drag & drop video file from SSD
                </div>
                <div class="dropzone-hint">Supports MP4, MKV, WebM up to 4K Ultra HD (Zero-RAM Streaming)</div>
              </div>
            </div>
          </div>
        ` : `
          <!-- BATCH QUEUE INPUT -->
          <div class="batch-input-grid">
            <div class="batch-hint-bar">
              <span>Paste multiple YouTube URLs (one URL per line). The background worker will download, transcribe, and render each sequentially.</span>
              <span class="badge-accent">Pre-downloading Enabled</span>
            </div>
            <textarea id="textareaBatchUrls" class="studio-textarea" rows="4" placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...">${state.batchUrlsText || ''}</textarea>
            <div class="batch-action-row">
              <button class="studio-btn studio-btn-primary" id="btnAddBatchQueue">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 8 12 12 14 14"></polyline></svg>
                Queue All Videos for Processing
              </button>
            </div>
          </div>
        `}

        <!-- Fast Inspection Preview Card (if inspected) -->
        ${insp ? `
          <div class="inspect-preview-card">
            <div class="inspect-thumb-wrapper">
              ${insp.thumbnail ? `<img src="${insp.thumbnail}" alt="Thumbnail" class="inspect-thumb">` : `<div class="inspect-thumb-placeholder">🎬</div>`}
              <span class="duration-badge">${insp.duration_str || '0s'}</span>
            </div>
            <div class="inspect-meta">
              <h3 class="inspect-title">${insp.title}</h3>
              <div class="inspect-tags">
                <span class="tag-pill tag-quality">${insp.quality_label || '1080p'}</span>
                ${insp.has_ultra ? '<span class="tag-pill tag-ultra">4K Ultra HD Available</span>' : ''}
                <span class="tag-pill tag-boxes">${insp.boxes_30s || 1} Potential 30s Shorts</span>
              </div>
            </div>
            <button class="inspect-dismiss" id="btnDismissInspect" title="Dismiss">×</button>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

