# WanderFM 🎵

Real-time AI music generation powered by **Google Lyria RealTime**, driven by your heartbeat, time of day, and local weather.

## Features

- **❤️ Heartbeat (BPM)** – Slider to simulate heart rate (60–180 BPM). Maps directly to music tempo.
- **🕐 Time of day** – Morning, afternoon, evening, and night shape the mood (e.g. calm morning vs late-night ambient).
- **🌤️ Weather** – Open-Meteo (free, no API key) influences style: sunny, rainy, cloudy, stormy, etc.

## Quick start

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Requires **Python 3.10+** (for google-genai Lyria support).

### 2. API key

Get a free key from [Google AI Studio](https://aistudio.google.com/apikey).

Create `.env`:

```
GOOGLE_API_KEY=your_key_here
```

Or enter it in the app when prompted.

### 3. Run

```bash
streamlit run app.py
```

### 4. Use

1. Enter your city for weather.
2. Adjust the heartbeat slider (BPM).
3. Click **Play** to start real-time music.
4. Move the slider while playing to change tempo.

## Project structure

```
src/
├── state.py    # MusicState – shared state (BPM, prompts, status)
├── audio.py    # Audio playback – queue → sounddevice
├── lyria.py    # Lyria API – connect, receive, apply config
├── runner.py   # Orchestrator – wires audio + Lyria
├── weather.py  # Open-Meteo API (no key)
└── prompts.py  # Time + weather → Lyria prompts
```

## Tech stack

- **Lyria RealTime** – Google’s real-time music model via `google-genai`
- **Open-Meteo** – Free weather API (no key)
- **Streamlit** – Web UI
- **sounddevice** – Audio playback

## Hackathon build (4h)

Built for a 4-hour hackathon.
