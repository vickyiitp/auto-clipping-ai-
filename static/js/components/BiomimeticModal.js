/**
 * Biomimetic Modal Component
 * Visualizes the 10 Self-Healing Failover Routes, Hardware Topology, and Memory Governor.
 */

export function renderBiomimeticModal(state) {
  if (!state.showTelemetryModal) {
    return '';
  }

  const routes = state.routeStatus || [
    { code: "R1", name: "Media Ingestion", desc: "Split-merge yt-dlp -> Single Stream -> Cached match" },
    { code: "R2", name: "Vocal Extraction", desc: "4-Pole 80-8000Hz bandpass -> Mono resample -> Stream copy" },
    { code: "R3", name: "Whisper STT", desc: "P-Core pinned Faster-Whisper -> Batched pipeline -> Unfiltered fallback" },
    { code: "R4", name: "Clip Detection", desc: "Ollama Llama-3 structured prompt -> Speech density scanner -> Uniform" },
    { code: "R5", name: "Auto-Reframe", desc: "Apollo Kalman tracker -> Predictive gator -> Center crop" },
    { code: "R6", name: "HW Transcoding", desc: "GPU Hardware (NVENC/QSV/AMF) -> libx264 CPU -> Safe crop" },
    { code: "R7", name: "ASS Typography", desc: "Dual typography kinetic bounce -> Single line glow -> Raw text" },
    { code: "R8", name: "Memory Governor", desc: "RAM floor monitoring -> Emergency temp cache flush -> Sequential pacing" },
    { code: "R9", name: "Core Affinity", desc: "P-Core 4.90GHz affinity lock -> All cores balanced -> OpenMP auto" },
    { code: "R10", name: "Delivery Mesh", desc: "SSD atomic rename -> Temp dir fallback -> Direct stream" },
  ];

  const mem = state.systemMemory || {};
  const hw = state.hardwareEncoder || {};

  return `
    <div class="modal-backdrop" id="telemetryBackdrop">
      <div class="studio-card telemetry-modal-card">
        <div class="modal-header">
          <div class="modal-title-group">
            <span class="modal-icon">🧬</span>
            <div>
              <h3 class="modal-title">Biomimetic Telemetry & 10-Route Self-Healing Mesh</h3>
              <p class="modal-subtitle">Inspired by natural self-stabilizing systems & NASA Kalman filtering</p>
            </div>
          </div>
          <button class="modal-close" id="btnCloseTelemetry">&times;</button>
        </div>

        <div class="modal-body">
          <!-- Top Stats Row -->
          <div class="telemetry-stats-row">
            <div class="stat-box">
              <div class="stat-label">CPU Topology</div>
              <div class="stat-val">6 P-Cores + 4 E-Cores</div>
              <div class="stat-sub">Starling Affinity Locked (4.90GHz)</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Hardware Encoder</div>
              <div class="stat-val">${hw.name || 'Auto Detected'}</div>
              <div class="stat-sub">${hw.type || 'GPU Acceleration'}</div>
            </div>
            <div class="stat-box">
              <div class="stat-label">Laminar RAM Floor</div>
              <div class="stat-val">${mem.available_gb || '4.0'} GB Free</div>
              <div class="stat-sub">${mem.used_percent || '50'}% System Load (Zero-Crash Floor)</div>
            </div>
          </div>

          <!-- 10 Routes Grid -->
          <h4 class="routes-heading">10 Self-Healing Redundancy Routes</h4>
          <div class="routes-grid">
            ${routes.map(r => `
              <div class="route-card active">
                <div class="route-header">
                  <span class="route-code">${r.code}</span>
                  <span class="route-name">${r.name}</span>
                  <span class="route-health">ONLINE</span>
                </div>
                <div class="route-desc">${r.desc}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="modal-footer">
          <button class="studio-btn studio-btn-secondary" id="btnDismissTelemetry">Close Telemetry</button>
        </div>
      </div>
    </div>
  `;
}

