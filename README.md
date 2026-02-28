# WanderFM 🎵

Real-time AI music generation powered by **Google Lyria RealTime**, driven by your heartbeat, time of day, local weather, and nearby places.

## Features

- **❤️ Heartbeat (BPM)** – Simulate heart rate (60–180 BPM). Maps directly to music tempo.
- **🕐 Time of day** – Morning, afternoon, evening, and night shape the mood (e.g. calm morning vs late-night ambient).
- **🌤️ Weather** – Google Weather API provides current conditions (sunny, rainy, cloudy, stormy, snowy, windy, etc.).
- **📍 Location** – Nearby places (via Google Places API) influence the music — a jazz club gets jazz, a stadium gets crowd energy, a park gets nature ambient. The place name itself is included in the prompt.

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

### 3. Run

You can choose between the CLI or the Web Interface:

**Web Interface (Premium):**
```bash
python server.py
```
Then open `http://localhost:8000` in your browser.

**CLI Version:**
```bash
python app.py
```

### 4. Use (Web Interface)

1. Adjust the **BPM slider** to change the tempo in real-time.
2. Enter coordinates or allow location access to update the mood based on local weather and nearby places.
3. Click **Play** to start the music generation.

## Project structure

```
src/
├── state.py      # MusicState – shared state (BPM, prompts, status)
├── audio.py      # Audio playback – queue → sounddevice
├── lyria.py      # Lyria API – connect, receive, apply config
├── runner.py     # Orchestrator – wires audio + Lyria
├── weather.py    # Google Weather API – current conditions
├── location.py   # Google Geocoding + Places – nearby place context
└── prompts.py    # Time + weather + location → Lyria prompts
```

## Tech stack

- **Lyria RealTime** – Google’s real-time music model via `google-genai`
- **Google Weather API** – Current weather conditions
- **Google Places API** – Nearby place context for location-aware prompts
- **sounddevice** – Audio playback

## Hackathon build (4h)

Built for a 4-hour hackathon.
