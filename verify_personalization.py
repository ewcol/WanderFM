import os
from dotenv import load_dotenv
from src.spotify import SpotifyClient
from src.prompts import get_spotify_style_prompts

def verify_spotify_integration():
    load_dotenv()
    
    print("--- Spotify Integration Verification ---")
    
    # Check credentials
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
    
    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing Spotify credentials in .env. Skipping API tests.")
        return

    print("✅ Spotify credentials found.")
    
    # 1. Test Spotify Client (requires manual OAuth if first time)
    print("\n1. Testing SpotifyClient fetching...")
    sp_client = SpotifyClient()
    if sp_client.authenticate():
        tracks = sp_client.get_personalized_tracks(limit=5)
        print(f"✅ Fetched {len(tracks)} tracks.")
        for t in tracks:
            print(f"   - {t['name']} by {t['artist']} ({t['type']})")
            
        # 2. Test Gemini Prompt Generation
        if tracks:
            print("\n2. Testing Gemini Prompt Generation...")
            prompts = get_spotify_style_prompts(tracks)
            if prompts:
                print("✅ Generated personalized prompts:")
                for text, weight in prompts:
                    print(f"   - {text} (weight: {weight})")
            else:
                print("❌ Failed to generate prompts via Gemini.")
    else:
        print("❌ Spotify authentication failed.")

if __name__ == "__main__":
    verify_spotify_integration()
