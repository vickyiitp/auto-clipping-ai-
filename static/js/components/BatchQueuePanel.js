/**
 * Batch Queue Panel Component
 * Displays the live multi-user queue state and scheduled video jobs.
 */

export function renderBatchQueuePanel(state) {
  const queueSummary = state.queueSummary || {};
  const waitingJobs = queueSummary.waiting_jobs || [];

  if (waitingJobs.length === 0) {
    return '';
  }

  return `
    <div class="studio-card queue-card" id="queueSection">
      <div class="section-header queue-header">
        <div>
          <h2 class="section-title">Batch Execution Queue (${waitingJobs.length} Pending)</h2>
          <span class="section-subtitle">Pipelined pre-downloading runs asynchronously while GPU processes sequentially</span>
        </div>
        <div>
          <button class="studio-btn studio-btn-ghost btn-sm" id="btnClearAllQueue">Clear Queue</button>
        </div>
      </div>

      <div class="queue-list">
        ${waitingJobs.map(item => `
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
        `).join('')}
      </div>
    </div>
  `;
}

