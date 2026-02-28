"""Convert time of day, weather, and location into Lyria text prompts."""

from datetime import datetime
from typing import Optional
import os
import logging
from google import genai
from src.weather import WeatherData

logger = logging.getLogger("WanderFM.Prompts")


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
    "gas_station":             ("driving road trip", 1.0),
    "rest_stop":               ("highway rest stop ambient", 1.0),
    # Entertainment & Recreation
    "amusement_park":          ("fun carnival upbeat", 1.4),
    "aquarium":                ("calm underwater ambient", 1.3),
    "bowling_alley":           ("retro bowling alley vibes", 1.2),
    "casino":                  ("casino lounge jazz", 1.4),
    "comedy_club":             ("playful upbeat comedy", 1.2),
    "concert_hall":            ("orchestral concert hall", 1.5),
    "city_park":               ("outdoor park nature", 1.3),
    "park":                    ("outdoor park nature", 1.3),
    "dog_park":                ("playful outdoor", 1.1),
    "hiking_area":             ("nature hiking ambient", 1.3),
    "live_music_venue":        ("live music venue energy", 1.6),
    "movie_theater":           ("cinematic dramatic", 1.3),
    "national_park":           ("wilderness nature ambient", 1.4),
    "night_club":              ("nightclub electronic dance", 1.6),
    "opera_house":             ("classical operatic", 1.5),
    "philharmonic_hall":       ("orchestral symphonic", 1.5),
    "state_park":              ("nature forest ambient", 1.3),
    "tourist_attraction":      ("iconic landmark ambient", 1.2),
    "vineyard":                ("wine country relaxed", 1.3),
    "water_park":              ("summer fun upbeat", 1.4),
    "zoo":                     ("playful world music", 1.2),
    "stadium":                 ("crowd energy sports", 1.5),
    "amphitheater":            ("outdoor live performance", 1.4),
    "amusement_center":        ("arcade retro electronic", 1.2),
    "botanical_garden":        ("serene garden ambient", 1.3),
    "karaoke":                 ("pop karaoke upbeat", 1.3),
    "marina":                  ("sailing sea breeze", 1.2),
    "observation_deck":        ("expansive panoramic ambient", 1.3),
    "roller_coaster":          ("thrilling excitement", 1.4),
    # Sports
    "arena":                   ("crowd energy sports", 1.5),
    "athletic_field":          ("outdoor sports energy", 1.3),
    "fitness_center":          ("energetic workout", 1.4),
    "golf_course":             ("calm pastoral", 1.1),
    "gym":                     ("energetic workout", 1.4),
    "ski_resort":              ("winter alpine", 1.4),
    "swimming_pool":           ("relaxed pool ambient", 1.1),
    "tennis_court":            ("active outdoor sports", 1.2),
    "playground":              ("playful upbeat", 1.1),
    # Food & Drink
    "bar":                     ("bar lounge", 1.4),
    "sports_bar":              ("energetic sports bar", 1.3),
    "lounge_bar":              ("smooth lounge jazz", 1.4),
    "irish_pub":               ("irish pub folk", 1.3),
    "pub":                     ("cozy pub folk", 1.3),
    "brewery":                 ("craft brewery casual", 1.2),
    "brewpub":                 ("craft beer casual", 1.2),
    "wine_bar":                ("smooth wine bar jazz", 1.4),
    "cocktail_bar":            ("cocktail bar smooth", 1.4),
    "beer_garden":             ("outdoor beer garden folk", 1.3),
    "hookah_bar":              ("lounge hookah chill", 1.2),
    "cafe":                    ("cozy cafe", 1.3),
    "coffee_shop":             ("cozy cafe", 1.3),
    "coffee_roastery":         ("artisan coffee ambient", 1.2),
    "tea_house":               ("calm tea ceremony", 1.2),
    "restaurant":              ("restaurant dining ambiance", 1.2),
    "fine_dining_restaurant":  ("elegant fine dining", 1.4),
    "fast_food_restaurant":    ("upbeat casual", 1.0),
    "japanese_restaurant":     ("japanese ambient", 1.3),
    "korean_restaurant":       ("korean pop ambient", 1.2),
    "french_restaurant":       ("french bossa nova", 1.3),
    "italian_restaurant":      ("italian romantic", 1.3),
    "mediterranean_restaurant":("mediterranean warm", 1.2),
    "mexican_restaurant":      ("latin rhythms", 1.3),
    "greek_restaurant":        ("mediterranean festive", 1.2),
    "indian_restaurant":       ("indian ambient raga", 1.3),
    "thai_restaurant":         ("southeast asian ambient", 1.2),
    "chinese_restaurant":      ("chinese ambient", 1.2),
    "sushi_restaurant":        ("japanese minimalist", 1.3),
    "bakery":                  ("warm cozy morning", 1.2),
    "dessert_shop":            ("sweet playful", 1.1),
    "ice_cream_shop":          ("cheerful summer", 1.1),
    # Culture
    "art_gallery":             ("contemplative modern art", 1.3),
    "art_museum":              ("contemplative cultural", 1.3),
    "history_museum":          ("historical ambient orchestral", 1.3),
    "museum":                  ("contemplative cultural", 1.3),
    "performing_arts_theater": ("theatrical dramatic", 1.4),
    "cultural_landmark":       ("cultural heritage", 1.2),
    "historical_landmark":     ("historical ambient", 1.2),
    "historical_place":        ("historical ambient", 1.2),
    "monument":                ("grand ceremonial", 1.2),
    # Nature
    "beach":                   ("beachside relaxation", 1.4),
    "lake":                    ("calm lakeside ambient", 1.3),
    "mountain_peak":           ("alpine mountain ambient", 1.4),
    "nature_preserve":         ("wildlife nature ambient", 1.3),
    "river":                   ("flowing river ambient", 1.2),
    "woods":                   ("forest nature ambient", 1.3),
    "scenic_spot":             ("scenic panoramic ambient", 1.2),
    "island":                  ("tropical island ambient", 1.3),
    # Education
    "library":                 ("quiet focused", 1.1),
    "university":              ("campus intellectual", 1.1),
    "school":                  ("youthful energetic", 1.1),
    # Places of Worship
    "church":                  ("reverent choral", 1.2),
    "mosque":                  ("peaceful spiritual", 1.2),
    "buddhist_temple":         ("meditative zen", 1.3),
    "hindu_temple":            ("devotional spiritual", 1.2),
    "synagogue":               ("reflective spiritual", 1.2),
    "shinto_shrine":           ("japanese spiritual", 1.3),
    # Lodging
    "hotel":                   ("hotel lobby ambient", 1.1),
    "resort_hotel":            ("resort relaxation", 1.2),
    "hostel":                  ("backpacker traveler vibes", 1.1),
    # Shopping
    "shopping_mall":           ("upbeat commercial pop", 1.1),
    "market":                  ("lively market world music", 1.3),
    "farmers_market":          ("folk outdoor market", 1.2),
    "flea_market":             ("eclectic vintage vibes", 1.1),
    # Transport
    "airport":                 ("transient global ambient", 1.1),
    "train_station":           ("urban transit ambient", 1.1),
    "subway_station":          ("urban underground ambient", 1.1),
    "ferry_terminal":          ("maritime sea ambient", 1.2),
}


def get_location_prompts(geocoded=None, nearby=None) -> list[tuple[str, float]]:
    """Generate prompts from nearby place and geocoded context."""
    prompts = []
    if nearby:
        # Include place name as a prompt for venue-specific flavor
        if nearby.name:
            prompts.append((f"{nearby.name} vibes", 1.5))
        if nearby.live_music:
            prompts.append(("live music venue energy", 1.8))
        if nearby.good_for_watching_sports:
            prompts.append(("energetic sports crowd", 1.5))
        if len(prompts) < 2 and nearby.primary_type and nearby.primary_type in _PLACE_TYPE_PROMPTS:
            prompts.append(_PLACE_TYPE_PROMPTS[nearby.primary_type])
        if not prompts and nearby.editorial_summary:
            prompts.append((nearby.editorial_summary[:60], 0.9))
        prompts.append((f"{geocoded.neighborhood} neighborhood", 0.7))
    return prompts[:2]


def get_spotify_style_prompts(tracks: list[dict]) -> list[tuple[str, float]]:
    """
    Use Gemini to summarize Spotify history into 3-5 musical style prompts.
    """
    if not tracks:
        logger.warning("⚠️ No tracks provided for Spotify style generation.")
        return []

    logger.info(f"🧠 Generating style prompts from {len(tracks)} Spotify tracks...")
    # Format tracks for the prompt
    track_list = "\n".join([f"- {t['name']} by {t['artist']} ({t['type']})" for t in tracks])
    
    prompt = f"""
    Based on the following list of recently played and liked songs from Spotify, 
    generate 3 to 5 short, descriptive Gemini Lyria musical style prompts.
    
    Lyria prompts should be descriptive, e.g., "Deep house with atmospheric pads", "Mellow acoustic folk", "Indie pop with bright synths".
    
    Output ONLY a comma-separated list of these prompts. Do not include any other text.
    
    Tracks:
    {track_list}
    """

    try:
        api_key = os.getenv("LYRIA_API_KEY")
        if not api_key:
            return []
            
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        if not response.text:
            logger.warning("⚠️ Gemini returned empty style response.")
            return []
            
        style_list = [s.strip() for s in response.text.split(",")]
        logger.info(f"✨ Gemini generated styles: {style_list}")
        # Assign weights, slightly higher for the first few
        weighted = []
        for i, style in enumerate(style_list[:3]):
             weight = 1.2 if i == 0 else (1.1 if i == 1 else 1.0)
             weighted.append((style, weight))
        return weighted
    except Exception as e:
        logger.error(f"❌ Gemini Prompt Generation Failed: {e}")
        return []


def build_combined_prompts(weather: WeatherData, bpm: int = 100, geocoded=None, nearby=None, *, genre: Optional[str] = None, experience: Optional[str] = None, spotify_prompts: list[tuple[str, float]] = None) -> list[tuple[str, float]]:
    """Combine time-of-day, weather, location, genre, and experience prompts for Lyria."""
    # Genre and experience get high-priority slots
    preference_prompts: list[tuple[str, float]] = []
    if genre:
        preference_prompts.append((f"{genre} style", 1.8))
    if experience:
        preference_prompts.append((f"{experience} mood", 1.8))

    # Reduce time/weather slots when preferences are active to stay within 6-prompt cap
    time_limit = 1 if preference_prompts else 2
    weather_limit = 1 if preference_prompts else 2

    time_prompts = [(t, w * 1.2) for t, w in get_time_of_day_prompts()][:time_limit]
    weather_prompts = get_weather_prompts(weather)[:weather_limit] if weather else []
    location_prompts = get_location_prompts(geocoded, nearby)

    # Mix in Spotify prompts if available
    personalized = spotify_prompts if spotify_prompts else []
    all_prompts = location_prompts + preference_prompts + personalized + time_prompts + weather_prompts
    logger.info(f"Building combined prompts: {all_prompts}")
    return filter_coherency(all_prompts, bpm)[:8]
