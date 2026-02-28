"""Convert time of day and weather into Lyria text prompts."""

from datetime import datetime
from src.weather import WeatherData


def get_time_of_day_prompts() -> list[tuple[str, float]]:
    """
    Map current time of day to weighted prompts.
    Returns list of (text, weight) for Lyria.
    """
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return [("gentle morning atmosphere", 1.5), ("soft ambient", 1.0), ("peaceful awakening", 0.8)]
    if 9 <= hour < 12:
        return [("bright energetic morning", 1.2), ("upbeat acoustic", 1.0), ("fresh and lively", 0.8)]
    if 12 <= hour < 14:
        return [("midday focus", 1.0), ("calm productivity", 1.2), ("minimal ambient", 0.8)]
    if 14 <= hour < 17:
        return [("afternoon warmth", 1.2), ("relaxed groove", 1.0), ("sunny vibes", 0.8)]
    if 17 <= hour < 20:
        return [("golden hour", 1.3), ("warm sunset", 1.0), ("mellow jazz", 0.7)]
    if 20 <= hour < 23:
        return [("evening chill", 1.2), ("lo-fi beats", 1.0), ("relaxing ambient", 0.9)]
    # 23-5: night
    return [("late night ambient", 1.5), ("dreamy atmospheric", 1.0), ("soft drone", 0.8)]


def get_weather_prompts(weather: WeatherData) -> list[tuple[str, float]]:
    """
    Map weather to weighted prompts.
    Returns list of (text, weight) for Lyria.
    """
    prompts = []
    cond = weather.condition
    temp = weather.temperature
    if cond == "sunny" or cond == "clear":
        prompts.append(("bright cheerful", 1.2))
        prompts.append(("sunny acoustic", 1.0))
    elif cond == "cloudy":
        prompts.append(("mellow overcast", 1.2))
        prompts.append(("soft ambient", 1.0))
    elif cond == "rainy":
        prompts.append(("rainy day ambient", 1.5))
        prompts.append(("cozy indoor", 1.0))
        prompts.append(("relaxing rain sounds texture", 0.8))
    elif cond == "snowy":
        prompts.append(("winter ambient", 1.3))
        prompts.append(("peaceful cold", 1.0))
    elif cond == "stormy":
        prompts.append(("dramatic atmospheric", 1.3))
        prompts.append(("intense ambient", 1.0))
    elif cond == "foggy":
        prompts.append(("misty ambient", 1.3))
        prompts.append(("ethereal drone", 1.0))
    else:
        prompts.append(("ambient", 1.0))

    # Temperature influence
    if temp > 30:
        prompts.append(("hot summer vibes", 0.6))
    elif temp < 0:
        prompts.append(("cold winter", 0.5))
    return prompts


def build_combined_prompts(weather: WeatherData) -> list[tuple[str, float]]:
    """Combine time-of-day and weather prompts for Lyria."""
    time_prompts = get_time_of_day_prompts()
    weather_prompts = get_weather_prompts(weather)
    # Merge: time gets slightly higher weight
    combined = [(t, w * 1.2) for t, w in time_prompts] + [(t, w) for t, w in weather_prompts]
    return combined[:6]  # Limit to avoid overload
