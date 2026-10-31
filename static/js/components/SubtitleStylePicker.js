/**
 * Subtitle Style & Kinetic Typography Picker Component
 * Curated preset cards + fine-grained video editor adjustments & color/size/width customizer.
 */

export function renderSubtitleStylePicker(state) {
  const presets = [
    {
      id: "aujle_tere_te",
      name: "✨ Aujle Golden Duo",
      desc: "Bold Modern Sans + Glowing Golden Calligraphy accent (Viral Karan Aujla vibe)",
      tag: "Trending Song Aesthetic",
      previewText: "TERE TE",
      previewAccent: "Aujle",
      dual: true,
      color: "#18C5F5",
      glow: "#0088FF",
    },
    {
      id: "kad_tera_rafal",
      name: "🌹 Rose Velvet Serif",
      desc: "Tall condensed Roman serif with romantic rose ambient aura",
      tag: "Editorial / Romance",
      previewText: "KAD TERA",
      previewAccent: "Rafal",
      dual: true,
      color: "#E8F0FF",
      glow: "#6633FF",
    },
    {
      id: "cyberpunk_neon",
      name: "⚡ Cyberpunk Neon Cyan",
      desc: "Electric Cyan highlight with intense neon magenta glow",
      tag: "Hype / EDM / Gaming",
      previewText: "KINETIC POP",
      dual: false,
      color: "#00FFFF",
      glow: "#FF00FF",
    },
    {
      id: "hormozi_white",
      name: "🤍 Hormozi Clean White",
      desc: "Bold Montserrat Black with deep black drop outline",
      tag: "Business / Podcast",
      previewText: "DISCIPLINE",
      dual: false,
      color: "#FFFF00",
      glow: "#000000",
    },
    {
      id: "never_imperial_echo",
      name: "⚔️ NEVER Echo Bodoni",
      desc: "Majestic Roman serif headline overlaid with delicate script echo",
      tag: "Imperial / High Drama",
      previewText: "NEVER",
      previewAccent: "Echoes",
      dual: true,
      color: "#20C0FF",
      glow: "#101830",
    },
    {
      id: "emerald_glow",
      name: "💚 Emerald Green Glow",
      desc: "High-retention vibrant emerald green with black shadow",
      tag: "Education / Tech",
      previewText: "RETENTION",
      dual: false,
      color: "#44FF00",
      glow: "#004400",
    },
  ];

  const currentPreset = state.subPreset || "aujle_tere_te";
  const subPos = state.subPosition || "bottom";

  // Active Colors
  const activeHighlight = state.customHighlightColor || "#FFFF00";
  const activePrimary   = state.customPrimaryColor   || "#FFFFFF";
  const activeGlow      = state.customGlowColor      || "#0088FF";

  // Active Dimensions & Typography Geometry
  const fontSize     = state.customFontSize || 65;
  const outlineWidth = state.customOutlineWidth !== undefined ? state.customOutlineWidth : 5;
  const shadowDepth  = state.customShadow !== undefined ? state.customShadow : 3;
  const isUppercase  = state.customUppercase !== false;

  const highlightSwatches = [
    "#FFFF00", "#FFB703", "#00F0FF", "#00FF66", "#FF007F", "#FF3366", "#FFFFFF"
  ];
  const primarySwatches = [
    "#FFFFFF", "#CBD5E1", "#FEF3C7", "#E0F2FE", "#FCE7F3"
  ];
  const glowSwatches = [
    "#000000", "#8000FF", "#0088FF", "#FF007F", "#FF8800", "#00FF44", "#3B82F6"
  ];

  return `
    <div class="studio-card subtitle-style-card">
      <div class="section-header">
        <h2 class="section-title">3. Viral Kinetic Typography, Preset Styles & Geometry</h2>
        <span class="section-subtitle">Google Fonts loaded natively by FFmpeg • Custom font size, stroke outline width, glow depth & colors</span>
      </div>

      <!-- Presets Grid -->
      <div class="presets-grid">
        ${presets.map(p => `
          <div class="preset-card ${currentPreset === p.id ? 'active' : ''}" data-preset="${p.id}" data-color="${p.color}" data-glow="${p.glow}">
            <div class="preset-badge">${p.tag}</div>
            <div class="preset-preview-box" style="box-shadow: 0 0 16px ${p.glow}33;">
              <span class="preview-headline" style="color: ${p.color}; text-shadow: 0 0 8px ${p.glow};">${p.previewText}</span>
              ${p.dual ? `<span class="preview-cursive" style="color: #ffd700; text-shadow: 0 0 6px rgba(255,215,0,0.6);">${p.previewAccent}</span>` : ''}
            </div>
            <div class="preset-name">${p.name}</div>
            <div class="preset-desc">${p.desc}</div>
          </div>
        `).join('')}
      </div>

      <!-- Text Editing: Font Size, Outline Width, Shadow Depth & Letter Casing -->
      <div class="dimensions-customizer-panel">
        <div class="dimension-panel-header">
          <div class="dimension-panel-title">
            <span class="dimension-icon">📐</span>
            <span>Subtitle Geometry: Font Size, Stroke Outline Width & Shadow</span>
          </div>
          <span class="dimension-panel-hint">Live sliders for pixel-perfect typography calibration</span>
        </div>

        <div class="dimensions-controls-grid">
          <!-- 1. Font Size (Text Size) -->
          <div class="dimension-box">
            <div class="dimension-box-header">
              <span class="dim-label">Font Size (Text Size)</span>
              <span class="dim-badge" id="lblFontSizeVal">${fontSize}px</span>
            </div>
            <div class="slider-wrapper">
              <input type="range" id="inputCustomFontSize" class="studio-slider" min="40" max="110" step="2" value="${fontSize}">
            </div>
            <div class="dim-quick-pills">
              <button type="button" class="dim-pill ${fontSize === 52 ? 'active' : ''}" data-type="size" data-val="52">Small 52px</button>
              <button type="button" class="dim-pill ${fontSize === 65 ? 'active' : ''}" data-type="size" data-val="65">Default 65px</button>
              <button type="button" class="dim-pill ${fontSize === 78 ? 'active' : ''}" data-type="size" data-val="78">Large 78px</button>
              <button type="button" class="dim-pill ${fontSize === 92 ? 'active' : ''}" data-type="size" data-val="92">Huge 92px</button>
            </div>
          </div>

          <!-- 2. Outline Width (Stroke Border Thickness) -->
          <div class="dimension-box">
            <div class="dimension-box-header">
              <span class="dim-label">Outline Width (Stroke Border)</span>
              <span class="dim-badge" id="lblOutlineWidthVal">${outlineWidth}px</span>
            </div>
            <div class="slider-wrapper">
              <input type="range" id="inputCustomOutlineWidth" class="studio-slider" min="0" max="12" step="1" value="${outlineWidth}">
            </div>
            <div class="dim-quick-pills">
              <button type="button" class="dim-pill ${outlineWidth === 0 ? 'active' : ''}" data-type="outline" data-val="0">None 0px</button>
              <button type="button" class="dim-pill ${outlineWidth === 3 ? 'active' : ''}" data-type="outline" data-val="3">Thin 3px</button>
              <button type="button" class="dim-pill ${outlineWidth === 5 ? 'active' : ''}" data-type="outline" data-val="5">Bold 5px</button>
              <button type="button" class="dim-pill ${outlineWidth === 8 ? 'active' : ''}" data-type="outline" data-val="8">Heavy 8px</button>
            </div>
          </div>

          <!-- 3. Shadow / Glow Depth & Letter Casing -->
          <div class="dimension-box">
            <div class="dimension-box-header">
              <span class="dim-label">Glow / Shadow Depth</span>
              <span class="dim-badge" id="lblShadowVal">${shadowDepth}px</span>
            </div>
            <div class="slider-wrapper">
              <input type="range" id="inputCustomShadow" class="studio-slider" min="0" max="10" step="1" value="${shadowDepth}">
            </div>
            <div class="casing-pills-row">
              <span class="casing-label">Casing:</span>
              <button type="button" class="casing-pill ${isUppercase ? 'active' : ''}" id="btnCaseUpper">ALL CAPS</button>
              <button type="button" class="casing-pill ${!isUppercase ? 'active' : ''}" id="btnCaseNormal">Normal Case</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Text & Glow Color Customizer Section -->
      <div class="color-customizer-panel">
        <div class="color-panel-header">
          <div class="color-panel-title">
            <span class="color-icon">🎨</span>
            <span>Subtitle Text & Glowing Aura Colors</span>
          </div>
          <span class="color-panel-hint">Pick any preset swatch or use the custom color wheel</span>
        </div>

        <div class="color-controls-grid">
          <!-- 1. Highlight Color (Active Bouncing Word) -->
          <div class="color-picker-box">
            <div class="color-box-label">
              <span>Active Word Color</span>
              <span class="color-code" id="lblHighlightHex">${activeHighlight}</span>
            </div>
            <div class="swatches-row">
              ${highlightSwatches.map(hex => `
                <button type="button" class="color-swatch-btn ${activeHighlight.toUpperCase() === hex.toUpperCase() ? 'active' : ''}" data-target="highlight" data-color="${hex}" style="background-color: ${hex};" title="${hex}"></button>
              `).join('')}
              <div class="custom-color-input-wrap" title="Custom color picker">
                <input type="color" id="inputCustomHighlight" class="native-color-picker" value="${activeHighlight}">
                <span class="picker-icon">🎯</span>
              </div>
            </div>
          </div>

          <!-- 2. Primary Text Color (Resting Inactive Words) -->
          <div class="color-picker-box">
            <div class="color-box-label">
              <span>Resting Words Color</span>
              <span class="color-code" id="lblPrimaryHex">${activePrimary}</span>
            </div>
            <div class="swatches-row">
              ${primarySwatches.map(hex => `
                <button type="button" class="color-swatch-btn ${activePrimary.toUpperCase() === hex.toUpperCase() ? 'active' : ''}" data-target="primary" data-color="${hex}" style="background-color: ${hex};" title="${hex}"></button>
              `).join('')}
              <div class="custom-color-input-wrap" title="Custom color picker">
                <input type="color" id="inputCustomPrimary" class="native-color-picker" value="${activePrimary}">
                <span class="picker-icon">🎯</span>
              </div>
            </div>
          </div>

          <!-- 3. Aura Glow Color -->
          <div class="color-picker-box">
            <div class="color-box-label">
              <span>Aura Glow & Outline</span>
              <span class="color-code" id="lblGlowHex">${activeGlow}</span>
            </div>
            <div class="swatches-row">
              ${glowSwatches.map(hex => `
                <button type="button" class="color-swatch-btn ${activeGlow.toUpperCase() === hex.toUpperCase() ? 'active' : ''}" data-target="glow" data-color="${hex}" style="background-color: ${hex};" title="${hex}"></button>
              `).join('')}
              <div class="custom-color-input-wrap" title="Custom color picker">
                <input type="color" id="inputCustomGlow" class="native-color-picker" value="${activeGlow}">
                <span class="picker-icon">🎯</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Live Subtitle Typography Preview Bar -->
        <div class="color-live-preview-box">
          <span class="live-preview-tag">LIVE COLOR & DIMENSION PREVIEW</span>
          <div class="live-preview-text-container">
            <span class="preview-word-highlight" id="liveWordHighlight" style="color: ${activeHighlight}; font-size: ${Math.round(fontSize * 0.35)}px; -webkit-text-stroke: ${Math.max(0, outlineWidth * 0.22)}px #000; text-transform: ${isUppercase ? 'uppercase' : 'none'}; text-shadow: 0 0 ${shadowDepth * 4}px ${activeGlow}, 0 0 4px #000, 0 0 2px #000;">VIRAL</span>
            <span class="preview-word-primary" id="liveWordPrimary" style="color: ${activePrimary}; font-size: ${Math.round(fontSize * 0.35)}px; -webkit-text-stroke: ${Math.max(0, outlineWidth * 0.22)}px #000; text-transform: ${isUppercase ? 'uppercase' : 'none'}; text-shadow: 0 0 4px #000, 0 0 2px #000;">KINETIC SUBTITLES</span>
          </div>
        </div>
      </div>

      <!-- Fine-grained Subtitle Position & Typography Controls -->
      <div class="sub-controls-row">
        <div class="sub-ctrl-group">
          <label class="ctrl-label">Subtitle Position:</label>
          <div class="position-pills">
            <button type="button" class="pos-pill ${subPos === 'bottom' ? 'active' : ''}" data-pos="bottom">Bottom (Default)</button>
            <button type="button" class="pos-pill ${subPos === 'center' ? 'active' : ''}" data-pos="center">Center / Middle</button>
            <button type="button" class="pos-pill ${subPos === 'top' ? 'active' : ''}" data-pos="top">Top</button>
          </div>
        </div>

        <div class="sub-ctrl-group">
          <label class="ctrl-label">Words Per Line:</label>
          <select id="selectWordsPerLine" class="studio-select-sm">
            <option value="1" ${state.customWordsPerLine == 1 ? 'selected' : ''}>1 Word (Fast Kinetic)</option>
            <option value="2" ${state.customWordsPerLine == 2 || !state.customWordsPerLine ? 'selected' : ''}>2 Words (Recommended)</option>
            <option value="3" ${state.customWordsPerLine == 3 ? 'selected' : ''}>3 Words</option>
          </select>
        </div>

        <div class="sub-ctrl-group">
          <label class="ctrl-label">Word-Pop Animation:</label>
          <div class="toggle-pill-wrapper">
            <input type="checkbox" id="checkWordPop" ${state.highlightWords !== false ? 'checked' : ''} class="studio-checkbox">
            <label for="checkWordPop" class="checkbox-label">Bounce 120% on Syllable Hit</label>
          </div>
        </div>
      </div>
    </div>
  `;
}
