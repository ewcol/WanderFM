"""
Audio playback via sounddevice.
Consumes PCM chunks from a queue and plays them through the system output.
"""

import queue
import threading
from typing import Optional

import sounddevice as sd

SAMPLE_RATE = 48000
CHANNELS = 2
DTYPE = "int16"


def create_player_thread(audio_queue: queue.Queue) -> threading.Thread:
    """
    Create and start a daemon thread that plays audio from the queue.
    Send None to the queue to stop the player.
    """
    def _run() -> None:
        stream: Optional[sd.RawOutputStream] = None
        try:
            stream = sd.RawOutputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=0,
            )
            stream.start()
            while True:
                chunk = audio_queue.get()
                if chunk is None:
                    break
                try:
                    stream.write(chunk)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            if stream:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
