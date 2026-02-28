"""Weather via Google Weather API (requires GOOGLE_API_KEY)."""

import os
import requests
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

WEATHER_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"

# Open-Meteo geocoding (used by CLI app only, no key needed)
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass
class WeatherData:
    """Weather data for music prompt generation."""
    temperature: float
    condition: str  # sunny, cloudy, rainy, snowy, stormy, foggy, windy
    description: str
    humidity: float
    wind_speed: float


# Google Weather condition type -> internal condition
_CONDITION_MAP: dict[str, str] = {
    "CLEAR":                    "sunny",
    "MOSTLY_CLEAR":             "sunny",
    "PARTLY_CLOUDY":            "cloudy",
    "MOSTLY_CLOUDY":            "cloudy",
    "CLOUDY":                   "cloudy",
    "WINDY":                    "windy",
    "WIND_AND_RAIN":            "stormy",
    "LIGHT_RAIN_SHOWERS":       "rainy",
    "CHANCE_OF_SHOWERS":        "rainy",
    "SCATTERED_SHOWERS":        "rainy",
    "RAIN_SHOWERS":             "rainy",
    "HEAVY_RAIN_SHOWERS":       "rainy",
    "LIGHT_TO_MODERATE_RAIN":   "rainy",
    "MODERATE_TO_HEAVY_RAIN":   "rainy",
    "RAIN":                     "rainy",
    "LIGHT_RAIN":               "rainy",
    "HEAVY_RAIN":               "rainy",
    "RAIN_PERIODICALLY_HEAVY":  "rainy",
    "LIGHT_SNOW_SHOWERS":       "snowy",
    "CHANCE_OF_SNOW_SHOWERS":   "snowy",
    "SCATTERED_SNOW_SHOWERS":   "snowy",
    "SNOW_SHOWERS":             "snowy",
    "HEAVY_SNOW_SHOWERS":       "snowy",
    "LIGHT_TO_MODERATE_SNOW":   "snowy",
    "MODERATE_TO_HEAVY_SNOW":   "snowy",
    "SNOW":                     "snowy",
    "LIGHT_SNOW":               "snowy",
    "HEAVY_SNOW":               "snowy",
    "SNOWSTORM":                "stormy",
    "SNOW_PERIODICALLY_HEAVY":  "snowy",
    "HEAVY_SNOW_STORM":         "stormy",
    "BLOWING_SNOW":             "snowy",
    "RAIN_AND_SNOW":            "snowy",
    "HAIL":                     "stormy",
    "HAIL_SHOWERS":             "stormy",
    "THUNDERSTORM":             "stormy",
    "THUNDERSHOWER":            "stormy",
    "LIGHT_THUNDERSTORM_RAIN":  "stormy",
    "SCATTERED_THUNDERSTORMS":  "stormy",
    "HEAVY_THUNDERSTORM":       "stormy",
}


def geocode_city(city: str) -> Optional[tuple[float, float]]:
    """Convert city name to (lat, lon). Returns None if not found."""
    resp = requests.get(GEOCODING_URL, params={"name": city, "count": 1}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    r = results[0]
    return (r["latitude"], r["longitude"])


def get_weather(lat: float, lon: float) -> WeatherData:
    """Fetch current weather from Google Weather API."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is not set. Add it to your .env file.")

    resp = requests.get(
        WEATHER_URL,
        params={
            "key": api_key,
            "location.latitude": lat,
            "location.longitude": lon,
        },
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()

    temp = data.get("temperature", {}).get("degrees", 0.0)
    humidity = data.get("relativeHumidity", 0)
    wind_speed = data.get("wind", {}).get("speed", {}).get("value", 0)

    condition_type = data.get("weatherCondition", {}).get("type", "CLEAR")
    condition = _CONDITION_MAP.get(condition_type, "clear")

    description_text = (
        data.get("weatherCondition", {}).get("description", {}).get("text", "")
    )

    return WeatherData(
        temperature=temp,
        condition=condition,
        description=description_text or condition,
        humidity=humidity,
        wind_speed=wind_speed,
    )
