import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger("WanderFM.Spotify")

class SpotifyClient:
    def __init__(self):
        self.scope = "user-library-read user-read-recently-played"
        self.sp = None

    def get_auth_manager(self):
        """Initialize and return the SpotifyOAuth manager."""
        # Prioritize SPOTIPY_ prefix as it's the official library convention
        client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI") or os.getenv("REDIRECT_URI")
        
        if not redirect_uri:
            redirect_uri = "http://127.0.0.1:8000/api/spotify/callback"
            
        logger.info(f"🛠️ Spotify Auth Manager init with Redirect URI: {redirect_uri}")
        if client_id:
            logger.info(f"🛠️ Spotify Client ID present: {client_id[:5]}...{client_id[-5:]}")
        else:
            logger.error("❌ Spotify Client ID is MISSING from environment!")

        return SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.scope,
            open_browser=False,
            cache_path=".spotify_cache"
        )

    def get_authorize_url(self):
        """Generate the URL for the user to visit to authorize the app."""
        auth_manager = self.get_auth_manager()
        return auth_manager.get_authorize_url()

    def authenticate_with_code(self, code):
        """Exchange the auth code for a token and initialize the client."""
        try:
            logger.info(f"🔄 Exchanging code for token...")
            auth_manager = self.get_auth_manager()
            auth_manager.get_access_token(code)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            user = self.sp.current_user()
            logger.info(f"✅ Spotify Authenticated as: {user['display_name']}")
            return True
        except Exception as e:
            logger.error(f"❌ Spotify Exchange failed: {e}")
            return False

    def authenticate(self):
        """Direct authentication (for CLI usage)."""
        try:
            auth_manager = self.get_auth_manager()
            token_info = auth_manager.get_cached_token()
            if token_info:
                logger.info("✅ Found cached Spotify token.")
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                return True
            logger.info("ℹ️ No cached Spotify token found.")
            return False
        except Exception as e:
            logger.error(f"❌ Spotify authentication Error: {e}")
            return False

    def get_personalized_tracks(self, limit=20):
        """
        Fetch recently played and liked songs.
        Returns a list of simplified track dictionaries.
        """
        if not self.sp:
            logger.warning("⚠️ No Spotify client initialized. Cannot fetch tracks.")
            return []

        tracks = []
        
        # 1. Get Recently Played
        try:
            recent = self.sp.current_user_recently_played(limit=limit)
            logger.info(f"🎵 Pulled {len(recent['items'])} recently played tracks:")
            for item in recent['items']:
                track = item['track']
                track_info = {'name': track['name'], 'artist': track['artists'][0]['name'], 'type': 'recently_played'}
                tracks.append(track_info)
                logger.info(f"   - {track_info['name']} by {track_info['artist']}")
        except Exception as e:
            logger.error(f"⚠️ Could not fetch recently played: {e}")

        # 2. Get Liked Songs
        try:
            liked = self.sp.current_user_saved_tracks(limit=limit)
            logger.info(f"❤️ Pulled {len(liked['items'])} liked songs:")
            for item in liked['items']:
                track = item['track']
                track_info = {'name': track['name'], 'artist': track['artists'][0]['name'], 'type': 'liked_song'}
                tracks.append(track_info)
                logger.info(f"   - {track_info['name']} by {track_info['artist']}")
        except Exception as e:
            logger.error(f"⚠️ Could not fetch liked songs: {e}")

        return tracks
