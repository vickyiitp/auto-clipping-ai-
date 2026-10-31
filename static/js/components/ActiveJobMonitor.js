/**
 * Active Job Monitor Component
 * Primary Action Button + Real-time progress bar, live SSE log console, and step badges.
 */

export function renderActiveJobMonitor(state) {
  const job = state.activeJob;
  const isRunning = job && (job.status === 'running' || job.status === 'queued' || job.status === 'downloading' || job.status === 'transcribing' || job.status === 'clipping' || job.status === 'rendering');
  const isCompleted = job && job.status === 'completed';
  const isFailed = job && job.status === 'failed';

  return `
    <div class="studio-card monitor-card" id="monitorSection">
      <!-- Main Generation Launch Trigger -->
      <div class="action-bar-container">
        <button class="studio-btn studio-btn-primary studio-btn-hero ${isRunning ? 'loading' : ''}" id="btnGenerateShorts" ${isRunning ? 'disabled' : ''}>
          ${isRunning ? `
            <span class="btn-spinner"></span>
            <span>Processing Video Pipeline (${job.progress || 0}%)...</span>
          ` : `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <span>Generate 9:16 Shorts with Kinetic Subtitles</span>
          `}
        </button>
      </div>

      <!-- Live Job Execution Card -->
      ${job ? `
        <div class="job-status-panel">
          <div class="job-header">
            <div class="job-meta-left">
              <span class="status-badge ${job.status}">
                <span class="pulse-dot"></span>
                ${job.status.toUpperCase()}
              </span>
              <span class="job-source-title">${job.video_title || 'Active Video'}</span>
            </div>
            <div class="job-meta-right">
              ${isRunning ? `
                <button class="studio-btn studio-btn-danger btn-sm" id="btnCancelActiveJob" data-jobid="${job.job_id}">
                  Cancel Job
                </button>
              ` : ''}
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="progress-container">
            <div class="progress-bar-track">
              <div class="progress-bar-fill" style="width: ${job.progress || 0}%;"></div>
            </div>
            <div class="progress-stats">
              <span class="current-step-label">${job.current_step || 'Initializing...'}</span>
              <span class="progress-percent">${job.progress || 0}%</span>
            </div>
          </div>

          <!-- Live Log Console -->
          <div class="console-wrapper">
            <div class="console-header">
              <div class="console-title">
                <span class="terminal-glyph">&gt;_</span>
                <span>Real-Time Biomimetic Execution Telemetry</span>
              </div>
              <div class="console-actions">
                <button class="console-btn" id="btnCopyLogs" title="Copy Logs to Clipboard">Copy</button>
                <button class="console-btn" id="btnClearLogsView" title="Clear Console View">Clear View</button>
              </div>
            </div>
            <div class="console-body" id="liveTerminalOutput">
              ${(job.recent_logs || job.logs || []).map(line => `
                <div class="log-line ${line.includes('❌') ? 'log-err' : line.includes('✅') ? 'log-ok' : ''}">${escapeHtml(line)}</div>
              `).join('')}
            </div>
          </div>
        </div>
      ` : ''}
    </div>
  `;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

