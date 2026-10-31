/**
 * Gallery View Component
 * Vertical 9:16 Shorts Video Cards with inline preview and batch download.
 */

export function renderGalleryView(state) {
  const shorts = state.gallery || [];

  return `
    <div class="studio-card gallery-card-panel" id="gallerySection">
      <div class="section-header gallery-header">
        <div>
          <h2 class="section-title">4. Generated 9:16 Shorts Gallery (${shorts.length})</h2>
          <span class="section-subtitle">Rendered at 1080x1920 with hardcoded kinetic subtitles and face centering</span>
        </div>
        <div class="gallery-actions">
          ${shorts.length > 0 ? `
            <a href="/api/download_zip" class="studio-btn studio-btn-primary btn-sm" id="btnDownloadZip">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Download All as .ZIP
            </a>
          ` : ''}
          <button class="studio-btn studio-btn-ghost btn-sm" id="btnRefreshGallery">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
            Refresh
          </button>
        </div>
      </div>

      ${shorts.length === 0 ? `
        <div class="gallery-empty-state">
          <div class="empty-icon">🎬</div>
          <div class="empty-title">No Shorts Generated Yet</div>
          <div class="empty-desc">Paste a YouTube URL above and click Generate to produce your first viral shorts.</div>
        </div>
      ` : `
        <div class="shorts-grid">
          ${shorts.map(s => `
            <div class="short-video-card">
              <div class="video-preview-wrapper">
                <video class="short-video-player" src="/api/stream_video/${encodeURIComponent(s.filename)}" preload="metadata" controls playsinline></video>
                <div class="short-meta-badge">${s.size_mb || '15'} MB</div>
              </div>
              <div class="short-card-info">
                <div class="short-title" title="${s.title || s.filename}">${s.title || s.filename}</div>
                <div class="short-actions-row">
                  <a href="/api/download/${encodeURIComponent(s.filename)}" class="studio-btn studio-btn-secondary btn-xs" download>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Download MP4
                  </a>
                  <button class="studio-btn studio-btn-ghost btn-xs text-danger btnDeleteShort" data-filename="${encodeURIComponent(s.filename)}">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `}
    </div>
  `;
}

