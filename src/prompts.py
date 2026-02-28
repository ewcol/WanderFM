"""Convert time of day and weather into Lyria text prompts."""

from datetime import datetime
from typing import Optional
from src.weather import WeatherData


def get_time_of_day_prompts() -> list[tuple[str, float]]:
    """
    Map current time of day to weighted prompts.
    Returns list of (text, weight) for Lyria.
    """
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return [("gentle morning atmosphere", 0.9), ("soft awakening", 0.7)]
    if 9 <= hour < 12:
        return [("bright energetic morning", 0.8), ("fresh and lively", 0.7)]
    if 12 <= hour < 14:
        return [("midday focus", 0.7), ("minimal ambient", 0.6)]
    if 14 <= hour < 17:
        return [("afternoon warmth", 0.8), ("sunny vibes", 0.6)]
    if 17 <= hour < 20:
        return [("golden hour sunset", 0.9), ("mellow sunset vibes", 0.7)]
    if 20 <= hour < 23:
        return [("evening chill", 0.8), ("relaxing background", 0.7)]
    # 23-5: night
    return [("late night ambient", 0.9), ("dreamy atmospheric", 0.7)]


def get_weather_prompts(weather: WeatherData) -> list[tuple[str, float]]:
    """
    Map weather to weighted prompts.
    Returns list of (text, weight) for Lyria.
    """
    prompts = []
    cond = weather.condition
    temp = weather.temperature
    if cond == "sunny" or cond == "clear":
        prompts.extend([("bright synths", 1.2), ("acoustic guitar", 1.1), ("higher frequencies", 1.0)])
    elif cond == "cloudy" or cond == "rainy":
        prompts.extend([("low pass filters", 1.2), ("warm textures", 1.1), ("rhodes piano", 1.0), ("more reverb", 0.9)])
    elif cond == "snowy":
        prompts.extend([("winter breeze", 1.1), ("peaceful cold", 1.0), ("soft crystalline textures", 0.8)])
    elif cond == "stormy":
        prompts.extend([("minor keys", 1.2), ("distorted textures", 1.1), ("aggressive bass", 1.0)])
    elif cond == "foggy":
        prompts.extend([("misty atmosphere", 1.1), ("ethereal drone", 1.0)])
    else:
        prompts.append(("ambient", 1.0))

    # Temperature influence
    if temp > 30:
        prompts.append(("warm summer heat", 0.6))
    elif temp < 0:
        prompts.append(("chilly winter crisp", 0.6))
    return prompts


def filter_coherency(prompts: list[tuple[str, float]], bpm: int) -> list[tuple[str, float]]:
    """
    Remove "soft" or "relaxing" prompts if the BPM is high (sports mode).
    Ensures the model doesn't get conflicting energy signals.
    """
    if bpm < 130:
        return prompts
        
    forbidden = {"ambient", "soft", "minimal", "gentle", "peaceful", "dreamy", "mellow", "chill", "relaxing", "cozy"}
    return [(t, w) for t, w in prompts if not any(word in t.lower() for word in forbidden)]


def build_combined_prompts(weather: Optional[WeatherData], bpm: int = 100) -> list[tuple[str, float]]:
    """Combine time-of-day and weather prompts for Lyria."""
    time_prompts = get_time_of_day_prompts()
    weather_prompts = get_weather_prompts(weather) if weather else []
    
    combined = time_prompts + weather_prompts
    return filter_coherency(combined, bpm)[:6]

def get_bpm_prompts(bpm: int) -> list[tuple[str, float]]:
    """
    Generate weighted prompts based on BPM to reinforce tempo.
    Uses exact value and high weights to ensure model compliance.
    """
    # High-priority exact BPM markers (Anchor Layer)
    prompts = [
        (f"exactly {bpm} bpm", 2.2),
        (f"tempo: {bpm} beats per minute", 1.8),
        (f"precise rhythmic pulse at {bpm} bpm", 1.5)
    ]
    
    if bpm < 80:
        prompts.extend([("slow steady pace", 1.0), ("relaxed tempo", 0.8)])
    elif bpm < 120:
        prompts.extend([("moderate rhythmic pulse", 1.0), ("steady consistent beat", 0.8)])
    else: # 120+
        prompts.extend([("fast energetic drive", 1.5), ("high tempo driving rhythm", 1.3)])
        
    return prompts
