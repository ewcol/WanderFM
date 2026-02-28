"""
Orchestrates the music playback thread.
Wires together audio player and Lyria session.
"""

import asyncio
import queue
import threading

from src.audio import create_player_thread
from src.lyria import run_session
from src.state import MusicState


def run_music_thread(api_key: str, state: MusicState) -> None:
    """
    Run Lyria session in a background thread.
    Starts audio player, connects to Lyria, streams audio.
    Sets state.running = False when done.
    """
    state.running = True
    state.error = None

    audio_queue: queue.Queue = queue.Queue()
    create_player_thread(audio_queue)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_session(api_key, state, audio_queue))
    finally:
        state.running = False
        loop.close()
