/**
 * AutoClip Studio — Client-side application logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const youtubeUrlInput = document.getElementById("youtubeUrl");
  const btnClearUrl = document.getElementById("btnClearUrl");
  const styleCardsContainer = document.getElementById("styleCardsContainer");
  const fontFamilySelect = document.getElementById("fontFamilySelect");
  const fontSizeRange = document.getElementById("fontSizeRange");
  const fontSizeDisplay = document.getElementById("fontSizeDisplay");
  const wordsPerLine = document.getElementById("wordsPerLine");
  const uppercaseToggle = document.getElementById("uppercaseToggle");
  const subPositionSelect = document.getElementById("subPositionSelect");
  const karaokeToggle = document.getElementById("karaokeToggle");
  const previewStage = document.getElementById("previewStage");
  const previewPositionBadge = document.getElementById("previewPositionBadge");
  const subtitlePreviewText = document.getElementById("subtitlePreviewText");

  let activeKaraokeIndex = 0;
  let karaokeInterval = null;

  const numClipsSelect = document.getElementById("numClips");
  const clipLengthSelect = document.getElementById("clipLength");
  const btnGenerate = document.getElementById("btnGenerate");
  const btnGenerateText = document.getElementById("btnGenerateText");

  const pipelineStepper = document.getElementById("pipelineStepper");
  const progressBar = document.getElementById("progressBar");
  const progressStatusText = document.getElementById("progressStatusText");
  const progressPercentage = document.getElementById("progressPercentage");
  const terminalLogs = document.getElementById("terminalLogs");
  const btnClearLogs = document.getElementById("btnClearLogs");

  const mainVideoPlayer = document.getElementById("mainVideoPlayer");
  const activeVideoName = document.getElementById("activeVideoName");
  const btnDownloadActive = document.getElementById("btnDownloadActive");
  const videoThumbnailsList = document.getElementById("videoThumbnailsList");
  const btnRefreshVideos = document.getElementById("btnRefreshVideos");
  const videoCountPill = document.getElementById("videoCountPill");
  const btnDownloadAllZip = document.getElementById("btnDownloadAllZip");

  const btnPresetSong = document.getElementById("btnPresetSong");
  const btnPresetZoo = document.getElementById("btnPresetZoo");

  // Video Source Tabs & Upload Elements
  const tabSourceYoutube = document.getElementById("tabSourceYoutube");
  const tabSourceUpload = document.getElementById("tabSourceUpload");
  const sectionYoutubeSource = document.getElementById("sectionYoutubeSource");
  const sectionUploadSource = document.getElementById("sectionUploadSource");
  const uploadDropzone = document.getElementById("uploadDropzone");
  const localVideoFileInput = document.getElementById("localVideoFileInput");
  const uploadProgressContainer = document.getElementById("uploadProgressContainer");
  const uploadProgressBar = document.getElementById("uploadProgressBar");
  const uploadProgressText = document.getElementById("uploadProgressText");
  const subLanguageModeSelect = document.getElementById("subLanguageModeSelect");

  let activeSourceType = "youtube"; // "youtube" | "upload"
  let activeUploadedVideoPath = null;
  let activeUploadedFilename = null;

  // Video Inspection & Strategy Elements
  const btnInspectVideo = document.getElementById("btnInspectVideo");
  const videoInfoBanner = document.getElementById("videoInfoBanner");
  const videoThumbImg = document.getElementById("videoThumbImg");
  const videoTitleDisplay = document.getElementById("videoTitleDisplay");
  const videoLengthDisplay = document.getElementById("videoLengthDisplay");
  const videoBoxesDisplay = document.getElementById("videoBoxesDisplay");
  const videoQualityDisplay = document.getElementById("videoQualityDisplay");
  const tabHighlights = document.getElementById("tabHighlights");
  const tabFullVideo = document.getElementById("tabFullVideo");
  const colNumClips = document.getElementById("colNumClips");
  const calcSummaryText = document.getElementById("calcSummaryText");
  const ramStatusBadge = document.getElementById("ramStatusBadge");
  const btnPurgeCache = document.getElementById("btnPurgeCache");
  const resourceModeSelect = document.getElementById("resourceModeSelect");
  const downloadResolutionSelect = document.getElementById("downloadResolutionSelect");
  const badgeDlSpeed = document.getElementById("badgeDlSpeed");

  let currentPresetId = "neon_cyber";
  let presetsData = {};
  let currentEventSource = null;
  let currentClippingMode = "smart_highlights";
  let inspectedDurationSec = 152;
  let inspectedTitle = 'GURU RANDHAWA - "AZUL" MV';

  // ── 1. Fetch & Initialize Presets ──────────────────────────────────────────
  async function loadPresets() {
    try {
      const res = await fetch("/api/presets");
      const data = await res.json();
      presetsData = data.presets || {};

      renderStyleCards(presetsData);
      updateSubtitlePreview();
    } catch (err) {
      console.error("Failed to load presets:", err);
    }
  }

  function renderStyleCards(presets) {
    styleCardsContainer.innerHTML = "";
    Object.entries(presets).forEach(([key, preset]) => {
      const card = document.createElement("div");
      card.className = `style-card ${key === currentPresetId ? "selected" : ""}`;
      card.dataset.id = key;

      let sampleStyle = getSampleCssForPreset(key, preset);

      card.innerHTML = `
        <div class="style-card-title">${preset.name}</div>
        <div class="style-card-desc">${preset.description}</div>
        <div class="style-card-sample" style="${sampleStyle}">
          ${key === "neon_cyber" ? "SING & SHINE 🎵" : "VIRAL HOOK 🔥"}
        </div>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".style-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        currentPresetId = key;

        // Apply preset defaults to inputs
        if (preset.font_name) fontFamilySelect.value = preset.font_name;
        if (preset.font_size) {
          fontSizeRange.value = preset.font_size;
          fontSizeDisplay.textContent = preset.font_size;
        }
        if (preset.words_per_line) wordsPerLine.value = preset.words_per_line;
        if (preset.uppercase !== undefined) uppercaseToggle.checked = preset.uppercase;

        updateSubtitlePreview();
      });

      styleCardsContainer.appendChild(card);
    });
  }

  function getSampleCssForPreset(key, preset) {
    const font = preset.font_name || "Impact";
    if (key === "tiktok_yellow") {
      return `font-family: '${font}', sans-serif; color: #facc15; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 3px 3px 6px rgba(0,0,0,0.8);`;
    } else if (key === "neon_cyber") {
      return `font-family: '${font}', sans-serif; color: #00ffff; text-shadow: -2px -2px 0 #3b0764, 2px -2px 0 #3b0764, -2px 2px 0 #3b0764, 2px 2px 0 #3b0764, 0 0 12px #00ffff;`;
    } else if (key === "hormozi_white") {
      return `font-family: '${font}', sans-serif; color: #ffffff; text-shadow: -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000, 4px 4px 6px rgba(0,0,0,0.9);`;
    } else if (key === "emerald_glow") {
      return `font-family: '${font}', sans-serif; color: #4ade80; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0 0 10px #22c55e;`;
    } else if (key === "sunset_fire") {
      return `font-family: '${font}', sans-serif; color: #fb923c; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000, 0 0 12px #ea580c;`;
    }
    return `font-family: '${font}', sans-serif; color: #ffffff; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;`;
  }

  // ── 2. Live Subtitle Preview ───────────────────────────────────────────────
  function updateSubtitlePreview() {
    const font = fontFamilySelect.value;
    const size = Math.round(fontSizeRange.value * 0.46);
    const uppercase = uppercaseToggle.checked;
    const position = subPositionSelect ? subPositionSelect.value : "bottom";
    const karaoke = karaokeToggle ? karaokeToggle.checked : true;
    const preset = presetsData[currentPresetId] || {};

    if (previewStage) {
      previewStage.className = `preview-stage pos-${position}`;
    }
    if (previewPositionBadge) {
      previewPositionBadge.textContent = `Position: ${position.toUpperCase()}`;
    }

    const sampleCss = getSampleCssForPreset(currentPresetId, preset);
    const words = uppercase ? ["FEEL", "THE", "RHYTHM"] : ["Feel", "the", "rhythm"];

    if (karaoke) {
      let html = "";
      words.forEach((w, idx) => {
        if (idx === activeKaraokeIndex) {
          html += `<span class="word-active" style="${sampleCss} font-size: ${size}px;">${w}</span> `;
        } else {
          html += `<span class="word-neutral" style="font-family: '${font}', sans-serif; font-size: ${size}px; color: #ffffff; text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;">${w}</span> `;
        }
      });
      subtitlePreviewText.innerHTML = html + " 🔥";
    } else {
      subtitlePreviewText.textContent = (uppercase ? "FEEL THE RHYTHM 🔥" : "Feel the rhythm 🔥");
      subtitlePreviewText.style.cssText = `${sampleCss} font-size: ${size}px;`;
    }
  }

  // Karaoke animated loop
  if (!karaokeInterval) {
    karaokeInterval = setInterval(() => {
      activeKaraokeIndex = (activeKaraokeIndex + 1) % 3;
      if (karaokeToggle && karaokeToggle.checked) {
        updateSubtitlePreview();
      }
    }, 650);
  }

  // Listeners for fine-tuning inputs
  fontFamilySelect.addEventListener("change", updateSubtitlePreview);
  fontSizeRange.addEventListener("input", (e) => {
    fontSizeDisplay.textContent = e.target.value;
    updateSubtitlePreview();
  });
  wordsPerLine.addEventListener("change", updateSubtitlePreview);
  uppercaseToggle.addEventListener("change", updateSubtitlePreview);
  if (subPositionSelect) subPositionSelect.addEventListener("change", updateSubtitlePreview);
  if (karaokeToggle) karaokeToggle.addEventListener("change", updateSubtitlePreview);

  // ── 3. Quick Fill Pills ───────────────────────────────────────────────────
  if (btnPresetSong) {
    btnPresetSong.addEventListener("click", () => {
      youtubeUrlInput.value = btnPresetSong.dataset.url;
      selectPresetById("neon_cyber");
      btnPresetSong.classList.add("active");
      if (btnPresetZoo) btnPresetZoo.classList.remove("active");
      resetDashboardForNewVideo(btnPresetSong.dataset.url);
    });
  }

  const genreSelectEl = document.getElementById("genreSelect");
  if (genreSelectEl) {
    genreSelectEl.addEventListener("change", () => {
      const g = genreSelectEl.value;
      if (g === "Motivational") {
        if (fontFamilySelect) fontFamilySelect.value = "Montserrat-Black";
        selectPresetById("tiktok_yellow");
      } else if (g === "Anime") {
        if (fontFamilySelect) fontFamilySelect.value = "BebasNeue-Regular";
        selectPresetById("sunset_fire");
      } else if (g === "Podcast") {
        if (fontFamilySelect) fontFamilySelect.value = "Poppins-ExtraBold";
        selectPresetById("emerald_glow");
      } else if (g === "Song") {
        if (fontFamilySelect) fontFamilySelect.value = "Oswald-Bold";
        selectPresetById("neon_cyber");
      } else if (g === "Movie") {
        if (fontFamilySelect) fontFamilySelect.value = "PlayfairDisplay-Bold";
        selectPresetById("hormozi_white");
      } else if (g === "Web Series") {
        if (fontFamilySelect) fontFamilySelect.value = "Cinzel-Bold";
        selectPresetById("hormozi_white");
      } else if (g === "Gaming") {
        if (fontFamilySelect) fontFamilySelect.value = "LuckiestGuy-Regular";
        selectPresetById("tiktok_yellow");
      } else if (g === "Educational") {
        if (fontFamilySelect) fontFamilySelect.value = "FiraCode-Bold";
        selectPresetById("emerald_glow");
      }
      if (wordsPerLine) wordsPerLine.value = "2";
      updateSubtitlePreview();
    });
  }

  if (btnPresetZoo) {
    btnPresetZoo.addEventListener("click", () => {
      youtubeUrlInput.value = btnPresetZoo.dataset.url;
      selectPresetById("tiktok_yellow");
      btnPresetZoo.classList.add("active");
      if (btnPresetSong) btnPresetSong.classList.remove("active");
      resetDashboardForNewVideo(btnPresetZoo.dataset.url);
    });
  }

  function selectPresetById(presetId) {
    currentPresetId = presetId;
    document.querySelectorAll(".style-card").forEach(card => {
      if (card.dataset.id === presetId) {
        card.click();
      }
    });
  }

  btnClearUrl.addEventListener("click", () => {
    youtubeUrlInput.value = "";
    youtubeUrlInput.focus();
    if (btnPresetSong) btnPresetSong.classList.remove("active");
    if (btnPresetZoo) btnPresetZoo.classList.remove("active");
    purgeMemoryAndCache(true);
    resetDashboardForNewVideo("");
  });

  youtubeUrlInput.addEventListener("change", () => {
    const val = youtubeUrlInput.value.trim();
    if (val) {
      resetDashboardForNewVideo(val);
    }
  });

  // ── Memory & Resource Optimization ──────────────────────────────────────
  async function fetchSystemStatus() {
    try {
      const res = await fetch("/api/system_status");
      if (!res.ok) return;
      const data = await res.json();
      const mem = data.memory || {};
      if (ramStatusBadge) {
        ramStatusBadge.innerHTML = `<span class="pulse-dot"></span> RAM: ${mem.available_gb || 0}GB Free (${mem.used_percent || 0}% used)`;
        if (mem.used_percent > 85) {
          ramStatusBadge.style.color = "#ef4444";
          ramStatusBadge.style.borderColor = "rgba(239,68,68,0.5)";
        } else {
          ramStatusBadge.style.color = "var(--accent-cyan)";
          ramStatusBadge.style.borderColor = "rgba(56,189,248,0.3)";
        }
      }
      if (btnPurgeCache) {
        if (data.temp_cache_mb > 0) {
          btnPurgeCache.textContent = `🧹 Purge Cache (${data.temp_cache_mb} MB)`;
        } else {
          btnPurgeCache.textContent = `🧹 Free RAM & Purge`;
        }
      }
    } catch (err) {
      console.warn("System status check failed:", err);
    }
  }

  async function purgeMemoryAndCache(silent = false) {
    try {
      const res = await fetch("/api/cleanup", { method: "POST" });
      const data = await res.json();
      fetchSystemStatus();
      if (!silent) {
        appendLog(`[Memory Optimization] Purged working cache: ${data.freed_mb} MB freed, RAM garbage collected.`, "success");
      }
    } catch (err) {
      console.warn("Purge cache failed:", err);
    }
  }

  function resetDashboardForNewVideo(url) {
    // Reset progress bar & stepper
    progressBar.style.width = "0%";
    progressPercentage.textContent = "0%";
    progressStatusText.textContent = "Ready to start";
    resetStepper();

    // Reset console & notify
    terminalLogs.innerHTML = "";
    if (url) {
      appendLog(`[System] New video source loaded: ${url}`, "info");
      inspectVideo(url);
    } else {
      appendLog(`[System] Input cleared. Memory cache purged.`, "info");
    }
    // Auto-purge intermediate cache from previous video
    purgeMemoryAndCache(true);
  }

  if (btnPurgeCache) {
    btnPurgeCache.addEventListener("click", () => {
      purgeMemoryAndCache(false);
    });
  }

  // ── Video Inspection & Box Calculations ──────────────────────────────────
  async function inspectVideo(url) {
    if (!url) return;
    if (btnInspectVideo) {
      btnInspectVideo.classList.add("loading");
      btnInspectVideo.innerHTML = `<span>⏳ Inspecting...</span>`;
    }
    try {
      const res = await fetch("/api/inspect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ youtube_url: url })
      });
      if (res.ok) {
        const data = await res.json();
        inspectedDurationSec = data.duration || data.duration_sec || 0;
        inspectedTitle = data.title || "YouTube Video";
        const durStr = data.duration_str || data.duration_formatted || `${inspectedDurationSec}s`;
        const thumbUrl = data.thumbnail || data.thumbnail_url || "";

        if (videoTitleDisplay) videoTitleDisplay.textContent = inspectedTitle;
        if (videoLengthDisplay) {
          videoLengthDisplay.textContent = `⏱️ Length: ${durStr} (${inspectedDurationSec}s)`;
        }
        if (videoThumbImg && thumbUrl) {
          videoThumbImg.src = thumbUrl;
        }
        if (videoQualityDisplay) {
          if (data.quality_label) {
            videoQualityDisplay.style.display = "inline-flex";
            videoQualityDisplay.textContent = `💎 Max: ${data.quality_label}`;
          } else {
            videoQualityDisplay.style.display = "none";
          }
        }
        if (downloadResolutionSelect) {
          if (data.has_ultra) {
            if (badgeDlSpeed) badgeDlSpeed.textContent = `💎 ${data.quality_label} Available`;
          } else if (inspectedDurationSec > 300) {
            if (badgeDlSpeed) badgeDlSpeed.textContent = "⚡ Fast";
          } else {
            if (badgeDlSpeed) badgeDlSpeed.textContent = "⚡ Fast";
          }
        }
        updateBoxCalculations();
        appendLog(`[Inspector] Video verified: "${inspectedTitle}" — Duration: ${durStr} | Max Quality: ${data.quality_label || 'Standard'}`, "info");
      }
    } catch (err) {
      console.warn("Inspect failed:", err);
    } finally {
      if (btnInspectVideo) {
        btnInspectVideo.classList.remove("loading");
        btnInspectVideo.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          Check Length
        `;
      }
    }
  }

  function updateBoxCalculations() {
    const chunk = parseInt(clipLengthSelect.value, 10) || 30;
    const totalBoxes = inspectedDurationSec > 0 ? Math.max(1, Math.ceil(inspectedDurationSec / chunk)) : 1;

    if (videoBoxesDisplay) {
      videoBoxesDisplay.textContent = `📦 ${totalBoxes} Boxes @ ${chunk}s`;
    }

    if (currentClippingMode === "full_video") {
      if (colNumClips) colNumClips.style.opacity = "0.45";
      if (calcSummaryText) {
        calcSummaryText.innerHTML = `<strong>Full Video Tiling:</strong> 100% of video (${inspectedDurationSec}s) divided into <strong>${totalBoxes} boxes</strong> (${chunk}s each) with <em>zero leftover</em>.`;
      }
    } else {
      const clips = parseInt(numClipsSelect.value, 10) || 3;
      if (colNumClips) colNumClips.style.opacity = "1";
      if (calcSummaryText) {
        calcSummaryText.innerHTML = `<strong>Smart Highlights:</strong> Extracting <strong>${clips} viral hooks</strong> (${chunk}s each) with speech snap-start.`;
      }
    }
  }

  if (btnInspectVideo) {
    btnInspectVideo.addEventListener("click", () => {
      inspectVideo(youtubeUrlInput.value.trim());
    });
  }

  if (tabHighlights && tabFullVideo) {
    tabHighlights.addEventListener("click", () => {
      tabHighlights.classList.add("active");
      tabFullVideo.classList.remove("active");
      currentClippingMode = "smart_highlights";
      updateBoxCalculations();
    });

    tabFullVideo.addEventListener("click", () => {
      tabFullVideo.classList.add("active");
      tabHighlights.classList.remove("active");
      currentClippingMode = "full_video";
      updateBoxCalculations();
    });
  }

  if (clipLengthSelect) {
    clipLengthSelect.addEventListener("change", updateBoxCalculations);
  }
  if (numClipsSelect) {
    numClipsSelect.addEventListener("change", updateBoxCalculations);
  }

  // ── Source Selection Tabs & Upload Handling ────────────────────────────
  if (tabSourceYoutube && tabSourceUpload) {
    tabSourceYoutube.addEventListener("click", () => {
      activeSourceType = "youtube";
      tabSourceYoutube.classList.add("active");
      tabSourceUpload.classList.remove("active");
      if (sectionYoutubeSource) sectionYoutubeSource.style.display = "block";
      if (sectionUploadSource) sectionUploadSource.style.display = "none";
    });

    tabSourceUpload.addEventListener("click", () => {
      activeSourceType = "upload";
      tabSourceUpload.classList.add("active");
      tabSourceYoutube.classList.remove("active");
      if (sectionUploadSource) sectionUploadSource.style.display = "block";
      if (sectionYoutubeSource) sectionYoutubeSource.style.display = "none";
    });
  }

  if (uploadDropzone && localVideoFileInput) {
    uploadDropzone.addEventListener("click", () => {
      localVideoFileInput.click();
    });

    localVideoFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadLocalFile(e.target.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      uploadDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadDropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      uploadDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadDropzone.classList.remove("dragover");
      });
    });

    uploadDropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadLocalFile(e.dataTransfer.files[0]);
      }
    });
  }

  function uploadLocalFile(file) {
    if (!file) return;

    if (uploadProgressContainer) uploadProgressContainer.style.display = "block";
    if (uploadProgressBar) uploadProgressBar.style.width = "0%";
    if (uploadProgressText) {
      uploadProgressText.style.display = "block";
      uploadProgressText.textContent = `Uploading ${file.name}... 0%`;
    }

    appendLog(`[Upload] Uploading "${file.name}" (${(file.size / (1024 * 1024)).toFixed(1)} MB)...`, "info");

    const formData = new FormData();
    formData.append("video", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/upload", true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        if (uploadProgressBar) uploadProgressBar.style.width = `${percent}%`;
        if (uploadProgressText) uploadProgressText.textContent = `Uploading ${file.name}... ${percent}%`;
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText);
          activeUploadedVideoPath = data.filepath;
          activeUploadedFilename = data.filename;
          inspectedDurationSec = Math.round(data.duration || 0);
          inspectedTitle = data.title || file.name;

          if (uploadProgressBar) uploadProgressBar.style.width = "100%";
          if (uploadProgressText) {
            uploadProgressText.textContent = `✓ Upload ready: ${data.filename} (${data.size_mb} MB)`;
          }

          if (videoInfoBanner) {
            videoInfoBanner.style.display = "flex";
            if (videoThumbImg && data.thumb_url) videoThumbImg.src = data.thumb_url;
            if (videoTitleDisplay) videoTitleDisplay.textContent = `📁 ${inspectedTitle}`;
            if (videoLengthDisplay) videoLengthDisplay.textContent = `⏱️ Length: ${data.duration_formatted} (${inspectedDurationSec}s)`;
            if (videoBoxesDisplay && data.box_splits) videoBoxesDisplay.textContent = `📦 ${data.box_splits['30s'] || 1} Boxes @ 30s`;
            if (videoQualityDisplay) {
              if (data.quality_tier) {
                videoQualityDisplay.style.display = "inline-flex";
                videoQualityDisplay.textContent = `💎 Max: ${data.quality_tier.toUpperCase()}`;
              } else {
                videoQualityDisplay.style.display = "none";
              }
            }
          }

          updateBoxCalculations();
          appendLog(`[Upload] File verified: "${inspectedTitle}" — Duration: ${data.duration_formatted}`, "success");
        } catch (err) {
          appendLog(`[Upload Error] Failed to parse response: ${err}`, "error");
          if (uploadProgressText) uploadProgressText.textContent = "Upload inspection failed.";
        }
      } else {
        appendLog(`[Upload Error] Server returned status ${xhr.status}`, "error");
        if (uploadProgressText) uploadProgressText.textContent = `Upload failed (${xhr.status}).`;
      }
    };

    xhr.onerror = () => {
      appendLog(`[Upload Error] Network connection error.`, "error");
      if (uploadProgressText) uploadProgressText.textContent = "Network error during upload.";
    };

    xhr.send(formData);
  }

  // ── 4. Fetch & Display Generated Videos ───────────────────────────────────
  async function loadVideos() {
    try {
      const res = await fetch("/api/videos");
      const data = await res.json();
      const videos = data.videos || [];
      renderVideosList(videos);

      if (videos.length > 0 && !mainVideoPlayer.getAttribute("src")) {
        setActiveVideo(videos[0]);
      }
    } catch (err) {
      console.error("Failed to load videos:", err);
    }
  }

  function renderVideosList(videos) {
    videoThumbnailsList.innerHTML = "";

    if (videoCountPill) {
      const totalMb = videos.reduce((acc, v) => acc + (parseFloat(v.size_mb) || 0), 0).toFixed(1);
      videoCountPill.textContent = `${videos.length} clip${videos.length === 1 ? '' : 's'} (${totalMb} MB)`;
    }
    if (btnDownloadAllZip) {
      btnDownloadAllZip.style.display = videos.length === 0 ? "none" : "inline-flex";
    }

    if (videos.length === 0) {
      videoThumbnailsList.innerHTML = `
        <div style="text-align: center; padding: 24px 10px; color: var(--text-dim); font-size: 13px;">
          No generated shorts yet.<br>Click "Generate 9:16 Shorts Now" to create your first one!
        </div>
      `;
      return;
    }

    videos.forEach((vid, idx) => {
      const item = document.createElement("div");
      item.className = "video-thumb-card";
      item.innerHTML = `
        <div class="thumb-info">
          <div class="thumb-title" title="${vid.filename}">📱 ${vid.filename}</div>
          <div class="thumb-sub">${vid.size_mb} MB • ${vid.created_at}</div>
        </div>
        <div class="thumb-actions" style="display:flex; align-items:center; gap:8px;">
          <a class="btn-thumb-download" href="${vid.download_url}" download="${vid.filename}" title="Download ${vid.filename}" onclick="event.stopPropagation();">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
          </a>
          <div class="btn-play-mini" title="Play Short">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
          </div>
        </div>
      `;

      item.addEventListener("click", () => {
        document.querySelectorAll(".video-thumb-card").forEach(c => c.classList.remove("active"));
        item.classList.add("active");
        setActiveVideo(vid);
      });

      videoThumbnailsList.appendChild(item);
    });
  }

  function setActiveVideo(vid) {
    const noVideoPlaceholder = document.getElementById("noVideoPlaceholder");
    const activeVideoMeta = document.getElementById("activeVideoMeta");
    if (noVideoPlaceholder) noVideoPlaceholder.style.display = "none";
    if (mainVideoPlayer) {
      mainVideoPlayer.style.display = "block";
      mainVideoPlayer.src = vid.url;
      mainVideoPlayer.load();
    }
    if (activeVideoMeta) activeVideoMeta.style.display = "flex";
    if (activeVideoName) activeVideoName.textContent = vid.filename;
    if (btnDownloadActive) {
      btnDownloadActive.href = vid.download_url;
      btnDownloadActive.setAttribute("download", vid.filename);
    }
  }

  btnRefreshVideos.addEventListener("click", loadVideos);

  // ── 5. Generation Pipeline Execution ─────────────────────────────────────
  btnGenerate.addEventListener("click", startGeneration);

  async function startGeneration() {
    let sourceLabel = "";
    let ytUrl = "";
    let localPath = "";

    if (activeSourceType === "upload") {
      if (!activeUploadedVideoPath) {
        alert("Please drop or browse a video file to upload first.");
        return;
      }
      localPath = activeUploadedVideoPath;
      sourceLabel = activeUploadedFilename || "Local Video";
    } else {
      ytUrl = youtubeUrlInput.value.trim();
      if (!ytUrl) {
        alert("Please enter or paste a YouTube URL first.");
        youtubeUrlInput.focus();
        return;
      }
      sourceLabel = ytUrl;
    }

    // Set UI to loading state
    setGeneratingState(true);
    resetStepper();
    appendLog(`[System] Initializing pipeline for: ${sourceLabel}`, "info");

    const genreSelect = document.getElementById("genreSelect");
    const payload = {
      youtube_url: ytUrl,
      local_video_path: localPath,
      genre: genreSelect ? genreSelect.value : "Podcast",
      clipping_mode: currentClippingMode,
      chunk_size_sec: parseInt(clipLengthSelect.value, 10),
      num_clips: parseInt(numClipsSelect.value, 10),
      clip_min_sec: parseInt(clipLengthSelect.value, 10),
      clip_max_sec: parseInt(clipLengthSelect.value, 10) + 15,
      sub_preset: currentPresetId,
      custom_sub_font: fontFamilySelect.value,
      custom_sub_size: parseInt(fontSizeRange.value, 10),
      custom_words_per_line: parseInt(wordsPerLine.value, 10),
      custom_uppercase: uppercaseToggle.checked,
      sub_position: subPositionSelect ? subPositionSelect.value : "bottom",
      highlight_words: karaokeToggle ? karaokeToggle.checked : true,
      resource_mode: resourceModeSelect ? resourceModeSelect.value : "balanced",
      download_resolution: downloadResolutionSelect ? downloadResolutionSelect.value : "720p",
      sub_language_mode: subLanguageModeSelect ? subLanguageModeSelect.value : "original",
    };

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || "Failed to start generation");
      }

      const { job_id } = await res.json();
      connectSseStream(job_id);
    } catch (err) {
      appendLog(`[Error] ${err.message}`, "error");
      setGeneratingState(false);
    }
  }

  function connectSseStream(jobId) {
    if (currentEventSource) {
      currentEventSource.close();
    }

    currentEventSource = new EventSource(`/api/stream/${jobId}`);

    currentEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.log) {
          appendLog(data.log);
          updateStepperFromLog(data.log);
        }
        if (data.progress !== undefined) {
          updateProgress(data.progress);
        }

        if (data.done) {
          currentEventSource.close();
          setGeneratingState(false);
          if (data.status === "failed") {
            appendLog("❌ Generation stopped due to an error. Please see logs above.", "error");
            progressStatusText.textContent = "Error occurred";
            return;
          }
          appendLog("🎉 Pipeline finished! All boxes ready.", "success");
          if (btnDownloadAllZip) {
            btnDownloadAllZip.href = `/api/download_batch_zip/${jobId}`;
            btnDownloadAllZip.setAttribute("download", `AutoClip_Batch_${jobId}.zip`);
            btnDownloadAllZip.innerHTML = `
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              📦 Download Batch (.ZIP)
            `;
          }
          appendLog("📦 Batch Archive Ready! Click '📦 Download Batch (.ZIP)' to download all clips in one folder.", "info");
          loadVideos();
          markAllStepsComplete();
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    currentEventSource.onerror = (err) => {
      console.warn("SSE connection closed or error:", err);
      // Fallback check status once
      setTimeout(() => checkJobStatus(jobId), 2000);
    };
  }

  async function checkJobStatus(jobId) {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      const data = await res.json();
      if (data.status === "completed" || data.status === "failed") {
        setGeneratingState(false);
        loadVideos();
      }
    } catch (err) {
      setGeneratingState(false);
    }
  }

  function setGeneratingState(isGenerating) {
    btnGenerate.disabled = isGenerating;
    if (isGenerating) {
      btnGenerateText.textContent = "Processing Short (Please wait)...";
    } else {
      btnGenerateText.textContent = "Generate 9:16 Shorts Now";
    }
  }

  function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressPercentage.textContent = `${percent}%`;

    if (percent < 20) progressStatusText.textContent = "Downloading YouTube Video...";
    else if (percent < 40) progressStatusText.textContent = "Extracting Audio Track...";
    else if (percent < 65) progressStatusText.textContent = "Transcribing with Faster-Whisper AI...";
    else if (percent < 80) progressStatusText.textContent = "Face Detection & 9:16 Crop Centering...";
    else if (percent < 95) progressStatusText.textContent = "Burning Stylish Subtitles & Rendering...";
    else progressStatusText.textContent = "Completed!";
  }

  function resetStepper() {
    document.querySelectorAll(".step-item").forEach(s => {
      s.classList.remove("active", "completed");
    });
    document.getElementById("stepDownload").classList.add("active");
  }

  function updateStepperFromLog(logText) {
    const l = logText.toLowerCase();
    const stepDownload = document.getElementById("stepDownload");
    const stepAudio = document.getElementById("stepAudio");
    const stepWhisper = document.getElementById("stepWhisper");
    const stepFace = document.getElementById("stepFace");
    const stepRender = document.getElementById("stepRender");

    if (l.includes("step 1") || l.includes("downloading")) {
      stepDownload.classList.add("active");
      if (logText.includes("Downloading:")) {
        const cleanStatus = logText.replace(/\[\d\d:\d\d:\d\d\]\s*/, '').trim();
        progressStatusText.textContent = cleanStatus;
      }
    } else if (l.includes("step 2") || l.includes("extracting audio")) {
      stepDownload.classList.remove("active");
      stepDownload.classList.add("completed");
      stepAudio.classList.add("active");
    } else if (l.includes("step 3") || l.includes("transcribing")) {
      stepAudio.classList.remove("active");
      stepAudio.classList.add("completed");
      stepWhisper.classList.add("active");
    } else if (l.includes("step 5") || l.includes("detecting faces") || l.includes("crop")) {
      stepWhisper.classList.remove("active");
      stepWhisper.classList.add("completed");
      stepFace.classList.add("active");
    } else if (l.includes("subtitles generated") || l.includes("rendering clip") || l.includes("encoding")) {
      stepFace.classList.remove("active");
      stepFace.classList.add("completed");
      stepRender.classList.add("active");
    }
  }

  function markAllStepsComplete() {
    document.querySelectorAll(".step-item").forEach(s => {
      s.classList.remove("active");
      s.classList.add("completed");
    });
  }

  function appendLog(message, type = "normal") {
    const line = document.createElement("div");
    line.className = `log-line ${type}`;

    if (message.includes("❌") || message.toLowerCase().includes("failed") || message.toLowerCase().includes("error")) {
      line.className = "log-line error";
    } else if (message.includes("✅") || message.includes("🎉") || message.toLowerCase().includes("saved")) {
      line.className = "log-line success";
    } else if (message.includes("⚠️")) {
      line.className = "log-line warn";
    }

    line.textContent = message;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }

  btnClearLogs.addEventListener("click", () => {
    terminalLogs.innerHTML = "";
  });

  // Initial load
  loadPresets();
  loadVideos();
  updateBoxCalculations();
  fetchSystemStatus();
  setInterval(fetchSystemStatus, 8000);
});
