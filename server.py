from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import threading
from typing import Optional
from dotenv import load_dotenv

from src.state import MusicState
from src.runner import run_music_thread
from src.weather import geocode_city, get_weather
from src.prompts import build_combined_prompts, get_time_of_day_prompts

load_dotenv()

app = FastAPI(title="WanderFM API")
state = MusicState()
music_thread: Optional[threading.Thread] = None
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

class UpdateRequest(BaseModel):
    bpm: Optional[int] = None
    city: Optional[str] = None

@app.get("/api/status")
async def get_status():
    return {
        "running": state.running,
        "bpm": state.bpm,
        "chunks_received": state.chunks_received,
        "error": state.error,
        "prompts": state.prompts,
        "city": getattr(state, "current_city", "Unknown")
    }

@app.post("/api/start")
async def start_music():
    global music_thread
    if state.running:
        return {"message": "Already running"}
    
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key missing")
    
    # Ensure prompts are set if not already
    if not state.prompts:
        state.prompts = build_combined_prompts(None, state.bpm)
    
    state.running = True
    state.error = None
    music_thread = threading.Thread(target=run_music_thread, args=(api_key, state))
    music_thread.daemon = True
    music_thread.start()
    return {"message": "Music started"}

@app.post("/api/stop")
async def stop_music():
    state.running = False
    return {"message": "Music stopping"}

@app.post("/api/update")
async def update_state(req: UpdateRequest):
    if req.bpm is not None:
        if 60 <= req.bpm <= 180:
            state.bpm = req.bpm
        else:
            raise HTTPException(status_code=400, detail="BPM must be 60-180")
    
    if req.city:
        coords = geocode_city(req.city)
        if coords:
            try:
                weather_data = get_weather(coords[0], coords[1])
                state.prompts = build_combined_prompts(weather_data, state.bpm)
                state.current_city = req.city
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            raise HTTPException(status_code=404, detail="City not found")
            
    return {"message": "Updated", "bpm": state.bpm, "city": getattr(state, "current_city", "Unknown")}

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
