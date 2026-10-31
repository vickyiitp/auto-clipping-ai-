/**
 * Studio Navbar Component
 * Enterprise header displaying brand, session ID, live hardware telemetry, and controls.
 */

export function renderNavbar(state) {
  const mem = state.systemMemory || {};
  const hw = state.hardwareEncoder || {};
  const isHealthy = (mem.status === 'healthy');

  return `
    <header class="studio-navbar">
      <div class="brand-lockup">
        <div class="brand-glyph">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
        </div>
        <div>
          <div class="brand-title">AUTOCLIP STUDIO <span class="brand-tag">ULTRA PRO</span></div>
          <div class="brand-subtitle">Zero-RAM Biomimetic Kinetic Pipeline • Multi-User Enterprise</div>
        </div>
      </div>

      <div class="navbar-actions">
        <!-- Multi-User Session Badge -->
        <div class="session-pill" title="Isolated Multi-User Workspace Session">
          <span class="pulse-dot"></span>
          <span class="session-label">Session:</span>
          <span class="session-code">${state.sessionId ? state.sessionId.slice(0, 8) : 'Default'}</span>
        </div>

        <!-- Hardware & Memory Pill -->
        <div class="telemetry-pill ${isHealthy ? 'healthy' : 'warning'}" id="btnOpenTelemetry" title="Click to view 10-Route Mesh & Hardware Topology">
          <span class="hw-icon">⚡</span>
          <span class="hw-encoder">${hw.type ? hw.type.split(' ')[0] : 'GPU HW'}</span>
          <span class="divider">/</span>
          <span class="hw-ram">${mem.available_gb || '4.0'}GB Free</span>
        </div>

        <!-- Clean Cache Button -->
        <button class="studio-btn studio-btn-ghost btn-sm" id="btnPurgeCache" title="Free temporary files from SSD">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          Purge Cache
        </button>

        <!-- View Gallery Toggle -->
        <button class="studio-btn studio-btn-secondary btn-sm" id="btnScrollGallery">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          Gallery (${state.gallery ? state.gallery.length : 0})
        </button>
      </div>
    </header>
  `;
}

