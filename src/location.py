"""Google Places & Geocoding integration for coordinate-based place context.

Provides two independent, coordinate-driven lookups:
- reverse_geocode(): high-level place context (neighborhood, city, country)
- search_nearby(): specific nearby locations with rich metadata
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
_NEARBY_FIELD_MASK = ",".join([
    "places.displayName",
    "places.types",
    "places.primaryType",
    "places.location",
    "places.id",
    "places.editorialSummary",
    "places.neighborhoodSummary",
    "places.liveMusic",
    "places.goodForWatchingSports",
    "places.currentOpeningHours",
    "places.priceLevel",
])
_REQUEST_TIMEOUT = 5


def _get_api_key() -> str:
    """Return the Google API key, raising early if it is missing."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. Add it to your .env file."
        )
    return key


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GeocodedPlace:
    """High-level geographic context resolved from coordinates."""

    formatted_address: str
    place_types: list[str] = field(default_factory=list)
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None  # ISO 3166-1 alpha-2


@dataclass(frozen=True)
class NearbyPlace:
    """A specific place near a set of coordinates."""

    name: str
    place_id: str
    primary_type: Optional[str] = None
    types: list[str] = field(default_factory=list)
    location: tuple[float, float] = (0.0, 0.0)
    editorial_summary: Optional[str] = None
    neighborhood_summary: Optional[str] = None
    live_music: Optional[bool] = None
    good_for_watching_sports: Optional[bool] = None
    currently_open: Optional[bool] = None
    price_level: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def reverse_geocode(lat: float, lon: float) -> Optional[GeocodedPlace]:
    """Resolve coordinates to place context via the Google Geocoding API.

    Returns None on empty results or any network/API error.
    """
    api_key = _get_api_key()

    try:
        resp = requests.get(
            _GEOCODE_URL,
            params={"latlng": f"{lat},{lon}", "key": api_key},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        log.exception("Geocoding request failed for (%s, %s)", lat, lon)
        return None

    status = data.get("status", "")
    if status != "OK":
        log.warning("Geocoding status %r for (%s, %s)", status, lat, lon)
        return None

    results = data.get("results", [])
    if not results:
        return None

    first = results[0]
    return GeocodedPlace(
        formatted_address=first.get("formatted_address", ""),
        place_types=first.get("types", []),
        neighborhood=_extract_component(first, "neighborhood"),
        city=(
            _extract_component(first, "locality")
            or _extract_component(first, "administrative_area_level_1")
        ),
        country=_extract_component(first, "country"),
        country_code=_extract_component(first, "country", short=True),
    )


def search_nearby(
    lat: float,
    lon: float,
    radius_meters: int = 100,
    max_results: int = 3,
) -> list[NearbyPlace]:
    """Find nearby places via the Google Places Nearby Search API.

    Returns an empty list on any network/API error.
    """
    api_key = _get_api_key()

    try:
        resp = requests.post(
            _NEARBY_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": _NEARBY_FIELD_MASK,
            },
            json={
                "maxResultCount": max_results,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lon},
                        "radius": radius_meters,
                    }
                },
            },
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        log.exception("Nearby search failed for (%s, %s)", lat, lon)
        return []

    return [_parse_nearby(p) for p in data.get("places", [])]


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _extract_component(
    result: dict, component_type: str, *, short: bool = False
) -> Optional[str]:
    """Pull a single value from the geocoding address_components array."""
    key = "short_name" if short else "long_name"
    for component in result.get("address_components", []):
        if component_type in component.get("types", []):
            return component.get(key)
    return None


def _parse_nearby(p: dict) -> NearbyPlace:
    """Convert a raw Places API dict into a NearbyPlace."""
    loc = p.get("location") or {}
    editorial = p.get("editorialSummary") or {}
    hood = p.get("neighborhoodSummary") or {}
    opening = p.get("currentOpeningHours") or {}

    return NearbyPlace(
        name=(p.get("displayName") or {}).get("text", ""),
        place_id=p.get("id", ""),
        primary_type=p.get("primaryType"),
        types=p.get("types", []),
        location=(loc.get("latitude", 0.0), loc.get("longitude", 0.0)),
        editorial_summary=editorial.get("text"),
        neighborhood_summary=hood.get("text"),
        live_music=p.get("liveMusic"),
        good_for_watching_sports=p.get("goodForWatchingSports"),
        currently_open=opening.get("openNow"),
        price_level=p.get("priceLevel"),
    )
