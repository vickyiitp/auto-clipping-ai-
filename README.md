<div align="center">

# ⚡ AutoClip AI Studio
### Autonomous Local AI Pipeline: Long-Form Videos ➔ Viral 9:16 Shorts, Reels & TikToks

<p align="center">
  <b>100% Free & Open-Source • 100% Local & Private • Zero Paid APIs • Unlimited High-Res Exports</b>
</p>

[![GitHub Stars](https://img.shields.io/github/stars/vickyiitp/auto-clipping-ai-?style=for-the-badge&logo=github&color=f59e0b)](https://github.com/vickyiitp/auto-clipping-ai-/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/vickyiitp/auto-clipping-ai-?style=for-the-badge&logo=github&color=3b82f6)](https://github.com/vickyiitp/auto-clipping-ai-/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/vickyiitp/auto-clipping-ai-?style=for-the-badge&color=ef4444)](https://github.com/vickyiitp/auto-clipping-ai-/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Follow @vickyiitp](https://img.shields.io/github/followers/vickyiitp?label=Follow%20%40vickyiitp&style=for-the-badge&logo=github&color=8b5cf6)](https://github.com/vickyiitp)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Ollama-Llama%203.1-orange?style=flat-square&logo=ollama" alt="Ollama" />
  <img src="https://img.shields.io/badge/Faster--Whisper-Word--Level%20AI-green?style=flat-square" alt="Faster Whisper" />
  <img src="https://img.shields.io/badge/OpenCV-Smart%20Face%20Track-red?style=flat-square&logo=opencv" alt="OpenCV" />
  <img src="https://img.shields.io/badge/FFmpeg-GPU%2FHardware%20Accel-black?style=flat-square&logo=ffmpeg" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/Flask-Web%20Studio%20UI-cyan?style=flat-square&logo=flask" alt="Flask" />
</p>

---

### 🌟 Stop Paying $30–$50/month for Cloud Clipping SaaS. Run it Locally for Free!

```
 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                                                                                 │
 │   16:9 Landscape YouTube Video / Podcast / Lecture                              │
 │   [████████████████████████████████████████████████] (60 Mins)                  │
 │                                                                                 │
 └────────────────────────────────────────┬────────────────────────────────────────┘
                                          │  Local AI Processing
                                          ▼
                ┌───────────────────────────────────────────────────┐
                │  🔥 3-5 Viral 9:16 Shorts with MrBeast Captions   │
                │  🎯 Auto Face Tracking (Speaker always centered)   │
                │  ⏱️ Word-by-Word Kinetic Subtitle Highlights      │
                │  🚀 Ready to upload to TikTok / Shorts / Reels    │
                └───────────────────────────────────────────────────┘
```

</div>

---

## ⚡ Why AutoClip AI? (SaaS vs. AutoClip)

| Feature | ❌ Opus Clip / Munch / Klap | ✅ AutoClip AI (This Project) |
| :--- | :---: | :---: |
| **Monthly Cost** | **$29 – $99 / month** | **$0.00 Free Forever (MIT License)** |
| **Usage Limits** | Strict monthly minutes / credits | **Unlimited Minutes & Clips** |
| **Privacy & Security** | Videos uploaded to third-party cloud | **100% Local & Private on your machine** |
| **API Keys Required** | Paid OpenAI / Claude / Cloud API keys | **Zero Paid APIs (Ollama + Whisper)** |
| **Video Resolution** | Watermarked or capped at 720p/1080p | **Original 1080p/4K Crisp Quality** |
| **Customization** | Rigid preset templates | **Full Code Control & CSS/ASS Subtitle Presets** |
| **Web Interface** | Proprietary SaaS | **Built-in Dark Mode Web Studio + Headless CLI** |

---

## 🚀 Insane Features & Superpowers

### 🧠 1. Autonomous Viral Moment Discovery (Local LLM)
- Uses **Ollama + Llama 3.1** (or DeepSeek, Mistral, Qwen) to evaluate transcripts for:
  - Strong psychological hooks (first 3 seconds)
  - Story climax and high emotional retention
  - Actionable punchlines and standalone coherence
- Outputs precise timestamps with title ideas, viral hook scores, and engagement summaries.

### 👁️ 2. Smart Computer Vision Face Tracking (Auto 9:16 Crop)
- Uses **OpenCV Haar Cascades + dynamic bounding-box smoothing** to detect active human faces.
- Computes optimal horizontal crop coordinates frame-by-frame with smooth inertia:
  - Never chops the speaker's face off the screen.
  - Automatically falls back to smart center-crop when no face is present.

### 🔥 3. MrBeast & Hormozi Kinetic Subtitles
- Generates professional `.ass` subtitle streams with **word-by-word active highlight karaoke**.
- Multiple built-in designer presets:
  - 🟡 **Hormozi Viral**: Bright yellow active word, punchy cyan, dark stroke.
  - 🔴 **MrBeast Pop**: Bold impact font, high-contrast red/yellow stroke, heavy drop shadow.
  - 🟢 **Cyberpunk Neon**: Neon green glow with electric accents.
  - ⚪ **Clean Minimalist**: Elegant white with subtle box background.
  - 👑 **Gold Executive**: Luxurious metallic gold gradients for business/finance clips.

### ⚡ 4. Blazing Fast Audio Transcription (Faster-Whisper)
- Powered by `faster-whisper` (CTranslate2 backend), running **up to 4x faster than vanilla Whisper** with half the memory footprint.
- Full GPU CUDA acceleration + automatic FP16 / INT8 quantization support.
- Produces exact word-level millisecond timestamps for precise caption sync.

### 💻 5. Dual-Mode: Sleek Web Studio UI + Power-User CLI
- **Modern Web App**: Built with Flask, vanilla CSS glassmorphism, real-time log streaming, live progress bar, interactive clip preview, and one-click ZIP exporter.
- **Headless CLI**: Run single commands or batch-process entire playlists in headless mode.

### 🛡️ 6. Hardware Resource Governor
- Auto-detects available CPU threads, GPU VRAM, and system memory.
- Safely manages chunk processing to prevent Out-Of-Memory (OOM) crashes on 8GB, 16GB, or 32GB machines.
- Built-in one-click cache purge for temporary media files.

---

## 🏗️ Architecture & Pipeline Flow

```
                      ┌──────────────────────┐
                      │  YouTube URL or File │
                      └──────────┬───────────┘
                                 │
                                 ▼
                     [ 1. yt-dlp Video Ingestion ]
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                     ▼                       ▼
            [ High-Res Video ]       [ 16kHz Mono WAV ]
                     │                       │
                     │                       ▼
                     │            [ 2. Faster-Whisper ]
                     │           (Word Timestamps STT)
                     │                       │
                     │                       ▼
                     │            [ 3. Local LLM / Ollama ]
                     │           (Llama 3.1 Hook Scoring)
                     │                       │
                     │                       ▼
                     │            [ Selected Viral Segments ]
                     │                       │
                     ▼                       ▼
         [ 4. OpenCV Face Tracking ]  [ 5. Kinetic Subtitle Engine ]
         (Dynamic Pan & Centering)    (Hormozi/MrBeast ASS Styles)
                     │                       │
                     └───────────┬───────────┘
                                 │
                                 ▼
                    [ 6. FFmpeg Hardware Render ]
                    (9:16 Crop + Burned Subtitles)
                                 │
                                 ▼
             🎉 9:16 Viral Shorts (output/ directory)
```

---

## 🛠️ Tech Stack & Tools

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Core Runtime** | Python 3.10+ | Orchestration, parallel threading, automation |
| **Video Downloader** | `yt-dlp` | High-fidelity YouTube video & audio extraction |
| **Speech-to-Text** | `faster-whisper` | Fast local transcription with word-level timestamps |
| **LLM Inference** | `ollama` (`llama3.1`) | Local AI prompt analysis, clip boundary selection |
| **Computer Vision** | `opencv-python` | Face detection, smart crop framing, smoothing |
| **Media Engine** | `FFmpeg` | Video slicing, 9:16 re-scaling, subtitle burn-in |
| **Web Server** | `Flask` | REST endpoints, SSE real-time log streaming |
| **Web UI** | Vanilla CSS3 + JS | Dark-mode glassmorphic dashboard, responsive layout |
| **Audio Processing** | `PyAV` / `ffmpeg` | 16kHz WAV conversion for Whisper optimization |

---

## ⚡ Quick Start Guide (Get Running in 60s)

### 1. Prerequisites

Make sure you have **FFmpeg** and **Ollama** installed on your system:

#### 🔧 Install FFmpeg
- **Windows**: Download from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/), extract, and add the `bin` folder to your system `Path`.
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt update && sudo apt install ffmpeg`

#### 🦙 Install Ollama & Pull Model
1. Download Ollama from [ollama.com](https://ollama.com)
2. Run this command to download the Llama 3.1 model:
```bash
ollama pull llama3.1
```

---

### 2. Clone & Setup Project

```bash
# 1. Clone this repository
git clone https://github.com/vickyiitp/auto-clipping-ai-.git
cd auto-clipping-ai-

# 2. Create and activate a virtual environment
# Windows:
python -m venv venv
venv\Scripts\activate

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

### 3. Launch the Studio!

#### 🌐 Option A: Launch Modern Web Studio (Recommended)
```bash
# Windows quick launcher:
run_web.bat

# Or run with Python:
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

#### 🖥️ Option B: Run Command-Line Pipeline
```bash
# Windows quick launcher:
run.bat

# Or direct CLI execution:
python main.py
```

---

## 🎨 Subtitle Presets Showcase

You can choose from several hand-tuned typography styles in the UI or configuration:

| Preset Name | Highlight Color | Font Family | Best Used For |
| :--- | :--- | :--- | :--- |
| **Hormozi Yellow** | Vivid Yellow (`#FFFF00`) | Montserrat Black | Business, Hustle, Podcasts |
| **MrBeast Impact** | Electric Red & Yellow | Impact / Komika | Entertainment, Reactions, High Energy |
| **Neon Cyber** | Electric Lime (`#00FF88`) | Arial Black | Tech, AI, Gaming, Web3 |
| **Minimal White** | Clean White + Box | Segoe UI Semibold | Documentaries, Storytelling, Education |
| **Gold Executive** | Warm Metallic Gold | Trebuchet MS Bold | Finance, Motivation, Luxury |

---

## 🗺️ Roadmap & Upcoming Crazy Features

- [x] **Local Whisper STT** with word-level millisecond accuracy
- [x] **Local Llama 3.1 integration** via Ollama for zero-cost semantic hook detection
- [x] **OpenCV Face Tracking** for automatic horizontal pan-and-scan
- [x] **Interactive Web Studio** with real-time SSE progress & video player
- [ ] **Multi-Speaker Split-Screen**: Dual-box camera layout for 2-person podcast interviews
- [ ] **Local AI B-Roll Insertion**: Automatically cut to relevant AI-generated imagery or stock footage
- [ ] **Background Music Auto-Ducking**: Add subtle lo-fi or phonk background tracks that duck under voice
- [ ] **One-Click Auto-Publisher**: Upload directly to YouTube Shorts, TikTok, and Instagram Reels API
- [ ] **Whisper-X / Diarization Support**: Native speaker attribution for multi-host shows

---

## 🤝 Contributing & Community

Contributions are what make the open-source community an amazing place to learn, inspire, and create! Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👨‍💻 Creator & Author

Built with ❤️ by **Vicky Kumar**

<p align="left">
  <a href="https://github.com/vickyiitp">
    <img src="https://img.shields.io/badge/GitHub-Follow%20%40vickyiitp-181717?style=for-the-badge&logo=github" alt="GitHub" />
  </a>
  <a href="mailto:vicky_24a12res1261@iitp.ac.in">
    <img src="https://img.shields.io/badge/Email-Contact%20Me-EA4335?style=for-the-badge&logo=gmail" alt="Email" />
  </a>
  <a href="https://github.com/vickyiitp/auto-clipping-ai-/stargazers">
    <img src="https://img.shields.io/badge/Support-Leave%20a%20Star%20%E2%AD%90-yellow?style=for-the-badge" alt="Star" />
  </a>
</p>

> 💬 **Have feedback or ideas for new AI features?** Open an [Issue](https://github.com/vickyiitp/auto-clipping-ai-/issues) or connect directly! If this project helped you save money on SaaS subscriptions, please give it a **⭐ Star** and follow!

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.
