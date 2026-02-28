# WanderFM 🎵

Real-time AI music generation powered by **Google Lyria RealTime**, driven by your heartbeat, time of day, local weather, and nearby places.

## Features

- **❤️ Heartbeat (BPM)** – Simulate heart rate (60–180 BPM). Maps directly to music tempo.
- **� Spotify Personalization** – Sync your listening history. Gemini analyzes your "Recently Played" tracks to generate personalized style prompts for Lyria.
- **�🎵 Genre** – Pick from presets (Lo-fi, Jazz, Electronic, Rock, Classical, R&B, Ambient, Japanese cryptopunk polka) or type your own for fine-grained control.
- **✨ Experience** – Choose a vibe (Happy Walk, Intense Study, Chill Evening, Road Trip, Workout) or describe your own to shape the music's energy and character.
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

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
# Google / Lyria API (Required)
GOOGLE_API_KEY=your_google_api_key
LYRIA_API_KEY=your_lyria_api_key # Can be the same as GOOGLE_API_KEY

# Spotify Personalization (Optional)
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://127.0.0.1:8000
```

#### How to get Spotify Credentials:
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Create a new App.
3. In the App settings, add `http://127.0.0.1:8000` to the **Redirect URIs**.
4. Copy the **Client ID** and **Client Secret** to your `.env` file.

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

1. **Genre & Experience** – Select presets or type custom values to steer the music's sound and character (applied with high priority).
2. Adjust the **BPM slider** to change the tempo in real-time.
3. **Spotify Sync** – Click "Sync Spotify Taste" to personalize the music based on your recent activity. A popup will guide you through authentication.
4. **Location** – Enter coordinates to update the mood based on local weather and nearby places. The location updates automatically as you type.
5. Click **Play** to start real-time music generation.

## Project structure

```
src/
├── state.py      # MusicState – shared state (BPM, prompts, status)
├── audio.py      # Audio playback – queue → sounddevice
├── lyria.py      # Lyria API – connect, receive, apply config
├── runner.py     # Orchestrator – wires audio + Lyria
├── spotify.py    # Spotify integration – fetch history + summarize
├── weather.py    # Google Weather API – current conditions
├── location.py   # Google Geocoding + Places – nearby place context
└── prompts.py    # Time + weather + location + context → Lyria prompts
```

## Tech stack

- **Lyria RealTime** – Google’s real-time music model via `google-genai`
- **Gemini 2.0 Flash** – Generates musical descriptions from Spotify data
- **Google Weather API** – Current weather conditions
- **Google Places API** – Nearby place context for location-aware prompts
- **Spotify API** – User listening history for personalization
- **sounddevice** – Audio playback

## Hackathon build (4h)

Built for a 4-hour hackathon.
