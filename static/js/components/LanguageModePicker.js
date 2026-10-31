/**
 * Language Mode Picker Component
 * Supports:
 * 1. 'original': Phonetic Romanized sing-along Latin letters (Zero Machine Translation, Hindi prompt anchored)
 * 2. 'en_translate': Semantic English translation
 */

export function renderLanguageModePicker(state) {
  const currentMode = state.subLanguageMode || "original";

  return `
    <div class="studio-card language-mode-card">
      <div class="section-header">
        <h2 class="section-title">2. Spoken Language & Subtitle Translation Router</h2>
        <span class="section-subtitle">Choose whether you want original sing-along lyrics or semantic English translation</span>
      </div>

      <div class="language-cards-grid">
        <!-- MODE 1: ORIGINAL SPOKEN (SING-ALONG) -->
        <div class="lang-card ${currentMode === 'original' ? 'active' : ''}" data-langmode="original" id="cardLangOriginal">
          <div class="lang-radio"></div>
          <div class="lang-body">
            <div class="lang-badge badge-green">Sing-Along Letters</div>
            <h3 class="lang-heading">🎵 Original Spoken (English Letters)</h3>
            <p class="lang-desc">
              Transcribes the exact native words spoken or sung into clean phonetic Romanized Latin letters (e.g., Hindi/Punjabi "Kudiye ni tere brown rang ne" instead of translating). Viewers can sing along!
            </p>
            <div class="lang-status-note">
              <span class="status-icon">🔒</span>
              <span><strong>Decoder Locked:</strong> Whisper Hindi/Gurmukhi anchor prevents English translation hallucination.</span>
            </div>
          </div>
        </div>

        <!-- MODE 2: ENGLISH TRANSLATION -->
        <div class="lang-card ${currentMode === 'en_translate' ? 'active' : ''}" data-langmode="en_translate" id="cardLangTranslate">
          <div class="lang-radio"></div>
          <div class="lang-body">
            <div class="lang-badge badge-blue">Global Meaning</div>
            <h3 class="lang-heading">🌐 English Translation</h3>
            <p class="lang-desc">
              Translates foreign speech and lyrics into fluent English subtitles so global viewers understand the meaning.
            </p>
            <div class="lang-status-note">
              <span class="status-icon">🌍</span>
              <span><strong>Global Audience:</strong> Ideal for educational content, interviews, and story-based videos.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

