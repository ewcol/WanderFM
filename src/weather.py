"""Free weather API using Open-Meteo (no API key required)."""

import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeatherData:
    """Weather data for music prompt generation."""
    temperature: float
    condition: str  # sunny, cloudy, rainy, snowy, stormy, foggy
    description: str
    humidity: float
    wind_speed: float


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> condition
# https://open-meteo.com/en/docs#api_form
WEATHER_CODES = {
    0: "sunny",
    1: "sunny",
    2: "cloudy",
    3: "cloudy",
    45: "foggy",
    48: "foggy",
    51: "rainy",
    53: "rainy",
    55: "rainy",
    61: "rainy",
    63: "rainy",
    65: "rainy",
    66: "rainy",
    67: "rainy",
    71: "snowy",
    73: "snowy",
    75: "snowy",
    77: "snowy",
    80: "rainy",
    81: "rainy",
    82: "rainy",
    85: "snowy",
    86: "snowy",
    95: "stormy",
    96: "stormy",
    99: "stormy",
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
    """Fetch current weather from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    curr = data["current"]
    code = int(curr.get("weather_code", 0))
    condition = WEATHER_CODES.get(code, "clear")
    return WeatherData(
        temperature=curr["temperature_2m"],
        condition=condition,
        description=_describe_condition(condition, curr["temperature_2m"]),
        humidity=curr["relative_humidity_2m"],
        wind_speed=curr["wind_speed_10m"],
    )


def _describe_condition(condition: str, temp: float) -> str:
    if condition in ("clear", "sunny"):
        return "sunny and clear"
    if condition == "cloudy":
        return "cloudy and overcast"
    if condition == "rainy":
        return "rainy"
    if condition == "snowy":
        return "snowy"
    if condition == "stormy":
        return "stormy with thunder"
    if condition == "foggy":
        return "foggy and misty"
    return "clear"
