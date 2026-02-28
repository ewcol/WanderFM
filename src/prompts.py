"""Convert time of day, weather, and location into Lyria text prompts."""

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
        prompts.append(("misty ambient", 1.3))
        prompts.append(("ethereal drone", 1.0))
    elif cond == "windy":
        prompts.append(("windswept open air", 1.2))
        prompts.append(("dynamic flowing", 1.0))
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

_PLACE_TYPE_PROMPTS: dict[str, tuple[str, float]] = {
    # Automotive
    "gas_station":             ("driving road trip", 0.7),
    "rest_stop":               ("highway rest stop ambient", 0.7),
    # Entertainment & Recreation
    "amusement_park":          ("fun carnival upbeat", 1.1),
    "aquarium":                ("calm underwater ambient", 1.0),
    "bowling_alley":           ("retro bowling alley vibes", 0.9),
    "casino":                  ("casino lounge jazz", 1.1),
    "comedy_club":             ("playful upbeat comedy", 0.9),
    "concert_hall":            ("orchestral concert hall", 1.2),
    "city_park":               ("outdoor park nature", 1.0),
    "park":                    ("outdoor park nature", 1.0),
    "dog_park":                ("playful outdoor", 0.8),
    "hiking_area":             ("nature hiking ambient", 1.0),
    "live_music_venue":        ("live music venue energy", 1.3),
    "movie_theater":           ("cinematic dramatic", 1.0),
    "national_park":           ("wilderness nature ambient", 1.1),
    "night_club":              ("nightclub electronic dance", 1.3),
    "opera_house":             ("classical operatic", 1.2),
    "philharmonic_hall":       ("orchestral symphonic", 1.2),
    "state_park":              ("nature forest ambient", 1.0),
    "tourist_attraction":      ("iconic landmark ambient", 0.9),
    "vineyard":                ("wine country relaxed", 1.0),
    "water_park":              ("summer fun upbeat", 1.1),
    "zoo":                     ("playful world music", 0.9),
    "stadium":                 ("crowd energy sports", 1.2),
    "amphitheater":            ("outdoor live performance", 1.1),
    "amusement_center":        ("arcade retro electronic", 0.9),
    "botanical_garden":        ("serene garden ambient", 1.0),
    "karaoke":                 ("pop karaoke upbeat", 1.0),
    "marina":                  ("sailing sea breeze", 0.9),
    "observation_deck":        ("expansive panoramic ambient", 1.0),
    "roller_coaster":          ("thrilling excitement", 1.1),
    # Sports
    "arena":                   ("crowd energy sports", 1.2),
    "athletic_field":          ("outdoor sports energy", 1.0),
    "fitness_center":          ("energetic workout", 1.1),
    "golf_course":             ("calm pastoral", 0.8),
    "gym":                     ("energetic workout", 1.1),
    "ski_resort":              ("winter alpine", 1.1),
    "swimming_pool":           ("relaxed pool ambient", 0.8),
    "tennis_court":            ("active outdoor sports", 0.9),
    "playground":              ("playful upbeat", 0.8),
    # Food & Drink
    "bar":                     ("bar lounge", 1.1),
    "sports_bar":              ("energetic sports bar", 1.0),
    "lounge_bar":              ("smooth lounge jazz", 1.1),
    "irish_pub":               ("irish pub folk", 1.0),
    "pub":                     ("cozy pub folk", 1.0),
    "brewery":                 ("craft brewery casual", 0.9),
    "brewpub":                 ("craft beer casual", 0.9),
    "wine_bar":                ("smooth wine bar jazz", 1.1),
    "cocktail_bar":            ("cocktail bar smooth", 1.1),
    "beer_garden":             ("outdoor beer garden folk", 1.0),
    "hookah_bar":              ("lounge hookah chill", 0.9),
    "cafe":                    ("cozy cafe", 1.0),
    "coffee_shop":             ("cozy cafe", 1.0),
    "coffee_roastery":         ("artisan coffee ambient", 0.9),
    "tea_house":               ("calm tea ceremony", 0.9),
    "restaurant":              ("restaurant dining ambiance", 0.9),
    "fine_dining_restaurant":  ("elegant fine dining", 1.1),
    "fast_food_restaurant":    ("upbeat casual", 0.7),
    "japanese_restaurant":     ("japanese ambient", 1.0),
    "korean_restaurant":       ("korean pop ambient", 0.9),
    "french_restaurant":       ("french bossa nova", 1.0),
    "italian_restaurant":      ("italian romantic", 1.0),
    "mediterranean_restaurant":("mediterranean warm", 0.9),
    "mexican_restaurant":      ("latin rhythms", 1.0),
    "greek_restaurant":        ("mediterranean festive", 0.9),
    "indian_restaurant":       ("indian ambient raga", 1.0),
    "thai_restaurant":         ("southeast asian ambient", 0.9),
    "chinese_restaurant":      ("chinese ambient", 0.9),
    "sushi_restaurant":        ("japanese minimalist", 1.0),
    "bakery":                  ("warm cozy morning", 0.9),
    "dessert_shop":            ("sweet playful", 0.8),
    "ice_cream_shop":          ("cheerful summer", 0.8),
    # Culture
    "art_gallery":             ("contemplative modern art", 1.0),
    "art_museum":              ("contemplative cultural", 1.0),
    "history_museum":          ("historical ambient orchestral", 1.0),
    "museum":                  ("contemplative cultural", 1.0),
    "performing_arts_theater": ("theatrical dramatic", 1.1),
    "cultural_landmark":       ("cultural heritage", 0.9),
    "historical_landmark":     ("historical ambient", 0.9),
    "historical_place":        ("historical ambient", 0.9),
    "monument":                ("grand ceremonial", 0.9),
    # Nature
    "beach":                   ("beachside relaxation", 1.1),
    "lake":                    ("calm lakeside ambient", 1.0),
    "mountain_peak":           ("alpine mountain ambient", 1.1),
    "nature_preserve":         ("wildlife nature ambient", 1.0),
    "river":                   ("flowing river ambient", 0.9),
    "woods":                   ("forest nature ambient", 1.0),
    "scenic_spot":             ("scenic panoramic ambient", 0.9),
    "island":                  ("tropical island ambient", 1.0),
    # Education
    "library":                 ("quiet focused", 0.8),
    "university":              ("campus intellectual", 0.8),
    "school":                  ("youthful energetic", 0.8),
    # Places of Worship
    "church":                  ("reverent choral", 0.9),
    "mosque":                  ("peaceful spiritual", 0.9),
    "buddhist_temple":         ("meditative zen", 1.0),
    "hindu_temple":            ("devotional spiritual", 0.9),
    "synagogue":               ("reflective spiritual", 0.9),
    "shinto_shrine":           ("japanese spiritual", 1.0),
    # Lodging
    "hotel":                   ("hotel lobby ambient", 0.8),
    "resort_hotel":            ("resort relaxation", 0.9),
    "hostel":                  ("backpacker traveler vibes", 0.8),
    # Shopping
    "shopping_mall":           ("upbeat commercial pop", 0.8),
    "market":                  ("lively market world music", 1.0),
    "farmers_market":          ("folk outdoor market", 0.9),
    "flea_market":             ("eclectic vintage vibes", 0.8),
    # Transport
    "airport":                 ("transient global ambient", 0.8),
    "train_station":           ("urban transit ambient", 0.8),
    "subway_station":          ("urban underground ambient", 0.8),
    "ferry_terminal":          ("maritime sea ambient", 0.9),
}


def get_location_prompts(geocoded=None, nearby=None) -> list[tuple[str, float]]:
    """Generate prompts from nearby place and geocoded context."""
    prompts = []
    if nearby:
        # Include place name as a prompt for venue-specific flavor
        if nearby.name:
            prompts.append((f"{nearby.name} vibes", 1.0))
        if nearby.live_music:
            prompts.append(("live music venue energy", 1.3))
        if nearby.good_for_watching_sports:
            prompts.append(("energetic sports crowd", 1.0))
        if len(prompts) < 2 and nearby.primary_type and nearby.primary_type in _PLACE_TYPE_PROMPTS:
            prompts.append(_PLACE_TYPE_PROMPTS[nearby.primary_type])
        if not prompts and nearby.editorial_summary:
            prompts.append((nearby.editorial_summary[:60], 0.9))
    if not prompts and geocoded and geocoded.neighborhood:
        prompts.append((f"{geocoded.neighborhood} neighborhood", 0.7))
    return prompts[:2]


def build_combined_prompts(weather: WeatherData, bpm: int = 100, geocoded=None, nearby=None, *, genre: Optional[str] = None, experience: Optional[str] = None) -> list[tuple[str, float]]:
    """Combine time-of-day, weather, location, genre, and experience prompts for Lyria."""
    # Genre and experience get high-priority slots
    preference_prompts: list[tuple[str, float]] = []
    if genre:
        preference_prompts.append((f"{genre} style", 1.5))
    if experience:
        preference_prompts.append((f"{experience} mood", 1.8))

    # Reduce time/weather slots when preferences are active to stay within 6-prompt cap
    time_limit = 1 if preference_prompts else 2
    weather_limit = 1 if preference_prompts else 2

    time_prompts = [(t, w * 1.2) for t, w in get_time_of_day_prompts()][:time_limit]
    weather_prompts = get_weather_prompts(weather)[:weather_limit] if weather else []
    location_prompts = get_location_prompts(geocoded, nearby)
    return filter_coherency(preference_prompts + time_prompts + weather_prompts + location_prompts, bpm)[:6]