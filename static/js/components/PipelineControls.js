/**
 * Pipeline Controls Component
 * Allows selecting the Genre (Music, Anime, Podcast, etc.), Clipping Mode, and Resolution.
 */

export function renderPipelineControls(state) {
  const genres = [
    { id: "Podcast", name: "🎙️ Podcast", desc: "Conversational hooks & provocative debates" },
    { id: "Song", name: "🎵 Song / MV", desc: "Peak chorus hooks & dynamic karaoke vibes" },
    { id: "Anime", name: "⚡ Anime", desc: "High-stakes battles & emotional awakenings" },
    { id: "Motivational", name: "🔥 Motivational", desc: "Mindset shifts & disciplined breakthroughs" },
    { id: "Movie", name: "🎬 Movie", desc: "Suspenseful scenes & dramatic cliffhangers" },
    { id: "Web Series", name: "📺 Web Series", desc: "Character clashes & dramatic cliffhangers" },
    { id: "Gaming", name: "🎮 Gaming", desc: "Clutch plays & energetic reaction rage" },
    { id: "Educational", name: "🧠 Educational", desc: "Rapid insights & mind-blowing facts" },
  ];

  const currentGenre = state.genre || "Podcast";
  const currentMode = state.clippingMode || "smart_highlights";
  const currentChunkSec = state.chunkSizeSec || "30";

  return `
    <div class="studio-card pipeline-controls-card">
      <div class="section-header">
        <h2 class="section-title">1. Content Genre & Smart Clipping Mode</h2>
        <span class="section-subtitle">Ollama Llama-3 adapts selection criteria specifically to your content</span>
      </div>

      <!-- Genre Selector Grid -->
      <div class="genre-grid">
        ${genres.map(g => `
          <div class="genre-card ${currentGenre === g.id ? 'active' : ''}" data-genre="${g.id}">
            <div class="genre-name">${g.name}</div>
            <div class="genre-desc">${g.desc}</div>
          </div>
        `).join('')}
      </div>

      <!-- Clipping Mode Cards -->
      <div class="mode-selection-row">
        <div class="mode-card ${currentMode === 'smart_highlights' ? 'active' : ''}" data-mode="smart_highlights" id="modeCardSmart">
          <div class="mode-radio"></div>
          <div class="mode-content">
            <div class="mode-title">✨ Smart AI Highlights (Recommended)</div>
            <div class="mode-desc">Ollama Llama-3 extracts viral hooks and peak audience-retention moments.</div>
            
            ${currentMode === 'smart_highlights' ? `
              <div class="mode-options-row">
                <div class="control-group">
                  <label>Number of Shorts:</label>
                  <select id="selectNumClips" class="studio-select-sm">
                    <option value="1" ${state.numClips == 1 ? 'selected' : ''}>1 Short</option>
                    <option value="2" ${state.numClips == 2 ? 'selected' : ''}>2 Shorts</option>
                    <option value="3" ${state.numClips == 3 || !state.numClips ? 'selected' : ''}>3 Shorts (Default)</option>
                    <option value="5" ${state.numClips == 5 ? 'selected' : ''}>5 Shorts</option>
                    <option value="10" ${state.numClips == 10 ? 'selected' : ''}>10 Shorts</option>
                  </select>
                </div>
                <div class="control-group">
                  <label>Duration Range:</label>
                  <span class="range-hint">30s – 60s per short</span>
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        <div class="mode-card ${currentMode === 'full_video' ? 'active' : ''}" data-mode="full_video" id="modeCardFull">
          <div class="mode-radio"></div>
          <div class="mode-content">
            <div class="mode-title">📦 Full Video Sequential Boxer (Zero-Missing Content)</div>
            <div class="mode-desc">Splits the entire video into consecutive sequential shorts (e.g., Part 1, Part 2...).</div>

            ${currentMode === 'full_video' ? `
              <div class="box-duration-pills">
                <label>Box Length:</label>
                <button type="button" class="duration-pill ${currentChunkSec === '15' ? 'active' : ''}" data-chunk="15">15s</button>
                <button type="button" class="duration-pill ${currentChunkSec === '30' ? 'active' : ''}" data-chunk="30">30s</button>
                <button type="button" class="duration-pill ${currentChunkSec === '45' ? 'active' : ''}" data-chunk="45">45s</button>
                <button type="button" class="duration-pill ${currentChunkSec === '60' ? 'active' : ''}" data-chunk="60">60s</button>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

