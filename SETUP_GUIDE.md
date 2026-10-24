# 🎬 Auto Clipping — Complete Setup & Usage Guide

> **Converts long YouTube videos into vertical 9:16 Shorts with burned-in subtitles.**
> 100% local. Zero paid APIs. Open source.

---

## 📋 What This Script Does (The Big Picture)

```
YouTube URL
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  yt-dlp     │────▶│ faster-      │────▶│  Ollama +   │
│  Download   │     │ whisper      │     │  Llama 3    │
│  video      │     │ Transcribe   │     │  Find clips │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                    ┌──────────────┐     ┌───────▼──────┐
                    │  FFmpeg      │◀────│  OpenCV      │
                    │  Crop + Subs │     │  Face detect │
                    └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    📱 9:16 Shorts (output/ folder)
```

---

## Phase 1: Zero-to-One Setup

### Step 1: Install External Tools (One-Time Setup)

These are programs that run **outside** Python. You need them installed on your computer:

#### 🔧 FFmpeg (Required)
FFmpeg is the engine that handles all video/audio processing.

**Windows:**
1. Go to [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Download **"ffmpeg-release-essentials.zip"**
3. Extract the ZIP file (right-click → "Extract All")
4. Inside the extracted folder, find the `bin` folder (e.g., `ffmpeg-7.0-essentials_build\bin`)
5. Copy the full path to that `bin` folder
6. Search "Environment Variables" in Windows Start menu → Click "Edit the system environment variables"
7. Click **"Environment Variables"** button → Under "System variables", find **Path** → Click **Edit**
8. Click **New** → Paste the `bin` folder path → Click **OK** on all dialogs
9. **Close and reopen** your terminal/PowerShell

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Verify it works:**
```bash
ffmpeg -version
```

#### 🦙 Ollama (Required)
Ollama runs AI models locally on your machine.

1. Go to [https://ollama.com/download](https://ollama.com/download) and install for your OS
2. Open a terminal and run:
```bash
ollama pull llama3.1
```
> This downloads the Llama 3.1 model (~4.7 GB). It only downloads once.

3. Ollama runs as a background service. To verify:
```bash
ollama list
```
You should see `llama3.1` in the list.

---

### Step 2: Open the Project Folder in Your Terminal

**Windows (PowerShell):**
```powershell
cd "e:\vickyiitp\Devil Labs\auto clipping"
```

**macOS / Linux:**
```bash
cd ~/Desktop/auto-clipping
```
> If you moved the project folder somewhere else, use that path instead.

---

### Step 3: Create a Python Virtual Environment

A virtual environment is a "sandbox" so this project's packages don't interfere with anything else on your computer.

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **If you get an error about "execution policy"**, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then try activating again.

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **How to know it's working:** Your terminal prompt will now show `(venv)` at the beginning.

---

### Step 4: Install Python Packages

With your virtual environment activated (you should see `(venv)` in your prompt):

```bash
pip install -r requirements.txt
```

This installs:
| Package | What It Does |
|---------|-------------|
| `yt-dlp` | Downloads YouTube videos |
| `faster-whisper` | Transcribes speech to text (locally) |
| `ollama` | Talks to the local Llama 3 model |
| `pydantic` | Validates the JSON output from Llama 3 |
| `opencv-python` | Detects faces in video frames |
| `ffmpeg-python` | Python wrapper for FFmpeg |

---

### Step 5: Place Your `cookies.txt` File (Optional)

> **You only need this if** you want to download age-restricted or login-required videos.

1. Install the browser extension **"Get cookies.txt LOCALLY"** (available for Chrome/Firefox)
2. Go to [youtube.com](https://youtube.com) and make sure you're logged in
3. Click the extension icon → "Export" → Save as `cookies.txt`
4. Move the `cookies.txt` file into the project folder:

```
auto clipping/
├── main.py           ← The script
├── requirements.txt  ← Package list
├── cookies.txt       ← PUT IT HERE (same level as main.py)
└── ...
```

---

## Phase 2: The Code

The complete script is in [`main.py`](file:///e:/vickyiitp/Devil%20Labs/auto%20clipping/main.py).

### Project Structure After Running

```
auto clipping/
├── main.py                  ← The script
├── requirements.txt         ← Package list
├── cookies.txt              ← (optional) YouTube cookies
│
├── downloads/               ← Created automatically
│   └── Video_Title.mp4      ← The downloaded YouTube video
│
├── temp/                    ← Created automatically
│   ├── full_audio.wav       ← Extracted audio
│   ├── full_transcript.txt  ← Full text transcript
│   ├── word_timestamps.json ← Every word with timing
│   ├── selected_clips.json  ← The clips Llama 3 chose
│   ├── clip_1_subtitles.ass ← Styled subtitle files
│   ├── clip_2_subtitles.ass
│   └── clip_3_subtitles.ass
│
└── output/                  ← Created automatically — YOUR FINAL SHORTS
    ├── short_1_Catchy_Title.mp4
    ├── short_2_Another_Title.mp4
    └── short_3_Best_Moment.mp4
```

### Key Design Decisions

| Feature | Implementation |
|---------|---------------|
| **Face detection fallback** | If no face is found in a segment, the script falls back to center-crop (so it never crashes) |
| **Subtitle fallback** | If subtitle burning fails (e.g., font issues), the script retries without subtitles |
| **LLM fallback** | If Ollama fails or returns bad data, the script creates evenly-spaced clips |
| **Structured output** | Uses Pydantic schemas with Ollama to guarantee valid JSON (no regex parsing) |
| **Word-level timing** | Subtitles are grouped into 6-word lines for readability on vertical screens |

---

## Phase 3: Execution & Troubleshooting

### Running the Script

**Make sure your virtual environment is activated** (you see `(venv)` in your prompt).

**Option A — Interactive mode (easiest):**
```bash
python main.py
```
The script will ask you to paste the YouTube URL.

**Option B — Pass the URL directly:**
```bash
python main.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

---

### What You Should See on Screen

```
╔════════════════════════════════════════════════════════════════════╗
║  AUTO CLIPPING — YouTube to Vertical Shorts Pipeline             ║
║  100% Local • Zero Paid APIs • Open Source                       ║
╚════════════════════════════════════════════════════════════════════╝

  🔎 Running pre-flight checks...
  ✓ Directory ready: ...\downloads
  ✓ Directory ready: ...\temp
  ✓ Directory ready: ...\output
  ✓ FFmpeg found
  ✓ Ollama is running (model: llama3.1)
  ✅ All systems go!

  ══════════════════════════════════════════════════════════════════
    📥  STEP 1: DOWNLOADING VIDEO
  ══════════════════════════════════════════════════════════════════
  [download] Downloading ...
  ✅ Downloaded: Video_Title.mp4

  ══════════════════════════════════════════════════════════════════
    🎵  STEP 2: EXTRACTING AUDIO
  ══════════════════════════════════════════════════════════════════
  ✅ Audio extracted: full_audio.wav

  ══════════════════════════════════════════════════════════════════
    🗣️  STEP 3: TRANSCRIBING AUDIO
  ══════════════════════════════════════════════════════════════════
  🌍 Detected language: en (confidence: 98.5%)
  ✅ Transcription complete!  Total words: 2,847

  ══════════════════════════════════════════════════════════════════
    🤖  STEP 4: FINDING BEST CLIPS
  ══════════════════════════════════════════════════════════════════
  📎 Clip 1: "The Shocking Truth"    120.0s → 165.0s (45.0s)
  📎 Clip 2: "Why Nobody Talks About"  340.0s → 395.0s (55.0s)
  📎 Clip 3: "The Real Reason"        580.0s → 620.0s (40.0s)

  ══════════════════════════════════════════════════════════════════
    🎥  STEP 5: PROCESSING CLIPS
  ══════════════════════════════════════════════════════════════════
  ✅ Face detected in 18/20 frames
  ✅ Subtitles generated: clip_1_subtitles.ass (8 lines)
  ✅ Saved: short_1_The_Shocking_Truth.mp4 (12.3 MB)
  ...

  🎉  PIPELINE COMPLETE!
  ✅ 3 Short(s) created in: ...\output
```

---

### ❗ Common Errors & How to Fix Them

#### Error 1: `'ffmpeg' is not recognized as an internal or external command`

**What it means:** FFmpeg is not installed or not in your system PATH.

**How to fix:**
1. Download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Extract the ZIP and find the `bin` folder
3. Add the `bin` folder path to your system PATH (see Step 1 above)
4. **Close and reopen** your terminal — this is critical!
5. Verify: `ffmpeg -version`

---

#### Error 2: `ConnectionError: Failed to connect to Ollama` / `Ollama NOT REACHABLE`

**What it means:** The Ollama server isn't running or the model isn't downloaded.

**How to fix:**
1. Open a **new terminal window** (separate from the one running the script)
2. Run: `ollama serve` (keep this terminal open)
3. In another terminal, run: `ollama pull llama3.1` (if you haven't already)
4. Verify: `ollama list` — you should see `llama3.1`
5. Now run the script again

> **Note:** On Windows, Ollama usually auto-starts as a background service after installation. If it doesn't, run `ollama serve` manually.

---

#### Error 3: `execution of .\venv\Scripts\Activate.ps1 is disabled on this system`

**What it means:** Windows PowerShell blocks scripts by default for security.

**How to fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating the virtual environment again:
```powershell
.\venv\Scripts\Activate.ps1
```

---

#### Error 4 (Bonus): `ModuleNotFoundError: No module named 'yt_dlp'`

**What it means:** You're running the script outside the virtual environment, or the packages aren't installed.

**How to fix:**
1. Make sure you see `(venv)` in your terminal prompt
2. If not, activate the venv:
   - Windows: `.\venv\Scripts\Activate.ps1`
   - macOS/Linux: `source venv/bin/activate`
3. Then install packages: `pip install -r requirements.txt`
4. Run the script: `python main.py`

---

## 🔧 Configuration Reference

All settings are in the `Config` class at the top of `main.py`. Here are the key ones:

| Setting | Default | What It Controls |
|---------|---------|-----------------|
| `WHISPER_MODEL_SIZE` | `"base"` | Transcription accuracy vs speed. Options: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `WHISPER_DEVICE` | `"cpu"` | Set to `"cuda"` if you have an NVIDIA GPU |
| `OLLAMA_MODEL` | `"llama3.1"` | Which Ollama model to use for clip selection |
| `NUM_CLIPS` | `3` | How many Shorts to generate |
| `CLIP_MIN_SEC` | `30` | Minimum clip length |
| `CLIP_MAX_SEC` | `60` | Maximum clip length |
| `TARGET_WIDTH` | `1080` | Output video width |
| `TARGET_HEIGHT` | `1920` | Output video height |
| `VIDEO_CRF` | `23` | Quality (lower = better, 18-28 is typical) |
| `FACE_SAMPLE_FRAMES` | `20` | More = better face tracking, slower |
| `SUB_FONT_SIZE` | `16` | Subtitle font size |

---

## 💡 Tips

- **First run is slowest** — Whisper downloads its model (~150 MB for "base") on the first run. Subsequent runs are much faster.
- **GPU acceleration** — If you have an NVIDIA GPU, change `WHISPER_DEVICE` to `"cuda"` and `WHISPER_COMPUTE` to `"float16"` for 5-10x faster transcription.
- **Longer videos** — For videos over 1 hour, consider using `WHISPER_MODEL_SIZE = "small"` for better accuracy.
- **Different languages** — Whisper auto-detects the language. It works with 99+ languages out of the box.
