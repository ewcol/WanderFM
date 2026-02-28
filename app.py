"""
WanderFM - Real-time music generation powered by Lyria (CLI Version)
Heartbeat (BPM) + Time of Day + Weather → Music
"""

import os
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

from src.state import MusicState
from src.runner import run_music_thread
from src.weather import geocode_city, get_weather
from src.prompts import build_combined_prompts, get_time_of_day_prompts

def main():
    load_dotenv()
    
    print("\n" + "="*30)
    print("      🎵 WanderFM (CLI)")
    print("="*30)
    print("Real-time music powered by Lyria")
    print("Heartbeat • Time • Weather\n")

    # Initialize state
    state = MusicState()
    
    # Lyria API Key (Google AI Studio - free at aistudio.google.com/apikey)
    lyria_api_key = os.getenv("LYRIA_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not lyria_api_key:
        print("❌ Error: Lyria API key not found. Please set LYRIA_API_KEY in your .env file.")
        return

    # Location for weather
    city = input("Enter city for weather (default: New York): ").strip() or "New York"
    
    # Fetch weather
    print(f"🔍 Fetching weather for {city}...")
    coords = geocode_city(city)
    weather_data = None
    if coords:
        try:
            weather_data = get_weather(coords[0], coords[1])
            print(f"✅ Weather: {weather_data.temperature:.0f}°C, {weather_data.description}")
        except Exception as e:
            print(f"⚠️ Could not fetch weather: {e}")
    else:
        print("⚠️ City not found. Using default prompts.")

    # Build prompts from time + weather
    state.prompts = build_combined_prompts(weather_data, state.bpm)
    
    now = datetime.now()
    print(f"🕒 Local Time: {now.strftime('%H:%M')} ({now.strftime('%A, %B %d')})")
    
    # Initial BPM
    try:
        bpm_input = input("Enter starting BPM (60-180, default: 90): ").strip()
        state.bpm = int(bpm_input) if bpm_input else 90
    except ValueError:
        state.bpm = 90
        print("⚠️ Invalid BPM. Using default: 90")

    # Start music thread
    print("\n🎹 Starting music generation...")
    state.running = True
    music_thread = threading.Thread(target=run_music_thread, args=(lyria_api_key, state))
    music_thread.daemon = True
    music_thread.start()

    print("\n" + "-"*30)
    print("🎵 Music is playing!")
    print("Commands:")
    print("  [Number] : Update BPM (e.g. '120')")
    print("  'q'      : Quit")
    print("-"*30)

    def input_thread_func(state):
        while state.running:
            try:
                cmd = input().strip().lower()
                if cmd == 'q':
                    state.running = False
                elif cmd.isdigit():
                    new_bpm = int(cmd)
                    if 60 <= new_bpm <= 180:
                        state.bpm = new_bpm
                        print(f"\n✅ BPM updated to {new_bpm}")
                    else:
                        print("\n⚠️ BPM must be between 60 and 180")
            except EOFError:
                state.running = False
                break

    in_thread = threading.Thread(target=input_thread_func, args=(state,))
    in_thread.daemon = True
    in_thread.start()

    try:
        last_status = ""
        while state.running:
            if state.error:
                print(f"\n❌ Error: {state.error}")
                state.running = False
                break
            
            prompt_text = " • ".join([f"{t} ({w:.1f})" for t, w in state.prompts[:3]])
            status = f"[BPM: {state.bpm:>3}] [Chunks: {state.chunks_received:>3}] {prompt_text[:40]}..."
            
            if status != last_status:
                print(f"\r{status}", end="", flush=True)
                last_status = status
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        state.running = False

    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
