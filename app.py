"""
WanderFM - Real-time music generation powered by Lyria
Heartbeat (BPM) + Time of Day + Weather → Music
"""

import os
import threading
import streamlit as st
from dotenv import load_dotenv

from src.state import MusicState
from src.runner import run_music_thread
from src.weather import geocode_city, get_weather
from src.prompts import build_combined_prompts

load_dotenv()

st.set_page_config(
    page_title="WanderFM",
    page_icon="🎵",
    layout="centered",
)

st.title("🎵 WanderFM")
st.caption("Real-time music powered by Lyria • Heartbeat • Time • Weather")

# Initialize session state
if "music_state" not in st.session_state:
    st.session_state.music_state = MusicState()
if "music_thread" not in st.session_state:
    st.session_state.music_thread = None

state = st.session_state.music_state

# API Key (Google AI Studio - free at aistudio.google.com/apikey)
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Location for weather
city = st.text_input("City for weather", value="New York", placeholder="e.g. London, Tokyo")

# Fetch weather
weather_data = None
if city:
    coords = geocode_city(city)
    if coords:
        try:
            weather_data = get_weather(coords[0], coords[1])
        except Exception as e:
            st.warning(f"Could not fetch weather: {e}")
    else:
        st.warning("City not found. Using default prompts.")

# Build prompts from time + weather
if weather_data:
    state.prompts = build_combined_prompts(weather_data)
else:
    from src.prompts import get_time_of_day_prompts
    state.prompts = get_time_of_day_prompts()

# UI
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("❤️ Heartbeat (BPM)")
    st.caption("Simulate your heart rate. 60–180 BPM maps to music tempo.")
    heartbeat = st.slider(
        "BPM",
        min_value=60,
        max_value=180,
        value=state.bpm,
        step=5,
        key="heartbeat_ui",
    )
    state.bpm = heartbeat

with col2:
    from datetime import datetime
    now = datetime.now()
    st.metric("Time", now.strftime("%H:%M"))
    st.caption(now.strftime("%A, %B %d"))
    if weather_data:
        st.metric("Weather", f"{weather_data.temperature:.0f}°C")
        st.caption(weather_data.description)

st.divider()

# Display active prompts
st.subheader("🎵 Music prompts")
prompt_text = " • ".join([f"{t} ({w:.1f})" for t, w in state.prompts[:4]])
st.info(prompt_text)

# Start / Stop
if state.running:
    st.success("🔊 Music playing — audio plays on this machine. Check system volume.")
    if state.chunks_received > 0:
        st.caption(f"Received {state.chunks_received} audio chunks")
    if state.last_applied_bpm is not None:
        st.caption(f"Tempo: {state.last_applied_bpm} BPM")
    if st.button("⏹ Stop music"):
        state.running = False
        st.rerun()
    if state.error:
        st.error(f"Error: {state.error}")
else:
    if st.button("▶ Play", type="primary"):
        if not api_key:
            st.error("Google AI Studio API key not found. Please set `GOOGLE_API_KEY` in your `.env` file.")
        else:
            state.running = True
            state.prompts = state.prompts  # ensure latest
            state.bpm = heartbeat
            t = threading.Thread(target=run_music_thread, args=(api_key, state))
            t.daemon = True
            t.start()
            st.session_state.music_thread = t
            st.rerun()

st.divider()
with st.expander("Troubleshooting"):
    st.markdown("""
- **No sound?** Audio plays on the machine running Streamlit. Run locally (`streamlit run app.py`) and check system volume.
- **Slider not changing music?** Move the slider and wait 1–2 seconds. Lyria needs a moment to apply tempo changes. Check that "Tempo: X BPM" updates when you move the slider.
- **Error shown?** Check your API key in your `.env` file. Lyria requires a valid Gemini API key.
- **Still stuck?** Move the heartbeat slider to refresh the page and see the latest status.
    """)
st.caption("Built with Lyria RealTime • Open-Meteo • Streamlit")
