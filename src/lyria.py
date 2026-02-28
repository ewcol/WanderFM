"""
Lyria RealTime API client.
Handles connection, audio extraction, and config updates.
"""

import asyncio
import logging
import queue
from typing import Any

from google import genai
from google.genai import types

from src.state import MusicState
from src.prompts import get_bpm_prompts, filter_coherency


MODEL = "models/lyria-realtime-exp"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WanderFM.Lyria")


def extract_audio_chunks(chunks: Any) -> list[bytes]:
    """
    Extract raw PCM bytes from Lyria audio_chunks.
    Handles both single object with .data and list of chunk objects.
    """
    out: list[bytes] = []
    if hasattr(chunks, "data") and chunks.data:
        d = chunks.data if isinstance(chunks.data, bytes) else bytes(chunks.data)
        out.append(d)
    elif hasattr(chunks, "__iter__") and not isinstance(chunks, (str, bytes)):
        for c in chunks:
            if hasattr(c, "data") and c.data:
                d = c.data if isinstance(c.data, bytes) else bytes(c.data)
                out.append(d)
    return out


async def receive_audio(
    session: Any,
    state: MusicState,
    audio_queue: queue.Queue,
) -> None:
    """
    Consume audio from Lyria session and put chunks into the queue.
    Runs until state.running is False.
    """
    try:
        logger.info("Listening for audio chunks...")
        while state.running:
            async for message in session.receive():
                if not state.running:
                    break
                sc = getattr(message, "server_content", None)
                if not sc:
                    continue
                chunks = getattr(sc, "audio_chunks", None)
                if not chunks:
                    continue
                for data in extract_audio_chunks(chunks):
                    if data:
                        state.chunks_received += 1
                        audio_queue.put(data)
            await asyncio.sleep(0.001)
    except Exception as e:
        logger.error(f"Error in receive_audio: {e}")
        state.error = str(e)


async def apply_config_updates(session: Any, state: MusicState) -> None:
    """
    Poll state and push BPM/prompt changes to Lyria.
    Runs until state.running is False.
    """
    last_bpm: int | None = None
    last_prompts: list[tuple[str, float]] | None = None

    while state.running:
        try:
            logger.debug("Checking for config updates...")
            current_bpm = state.bpm
            current_prompts = state.prompts

            if current_bpm != last_bpm:
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(
                        bpm=current_bpm,
                        temperature=0.9,
                    )
                )
                await session.reset_context()
                last_bpm = current_bpm
                state.last_applied_bpm = current_bpm
                logger.info(f"Sent BPM update to Lyria: {current_bpm} BPM")
                
                # Force prompt update when BPM changes to reinforce tempo
                last_prompts = None 

            if current_prompts and (current_prompts != last_prompts or last_bpm == current_bpm):
                # Apply coherency filter reactively (e.g. remove "soft" prompts if HR is high)
                filtered_prompts = filter_coherency(current_prompts, current_bpm)
                bpm_prompts = get_bpm_prompts(current_bpm)
                weighted = [
                    types.WeightedPrompt(text=t, weight=w)
                    for t, w in (filtered_prompts + bpm_prompts)
                ]
                await session.set_weighted_prompts(prompts=weighted)
                last_prompts = current_prompts.copy()
                logger.info(f"Sent weighted prompts: {[p.text for p in weighted]}")

        except Exception as e:
            logger.error(f"Error in apply_config_updates: {e}")
            state.error = str(e)
        await asyncio.sleep(0.5)


async def run_session(
    api_key: str,
    state: MusicState,
    audio_queue: queue.Queue,
) -> None:
    """
    Connect to Lyria, start playback, and run receive + config loops.
    Puts None into audio_queue when done (signals player to stop).
    """
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1alpha"),
    )
    logger.info(f"Connecting to Lyria session (model: {MODEL})...")
    try:
        async with client.aio.live.music.connect(model=MODEL) as session:
            user_prompts = state.prompts or [("ambient", 1.0)]
            # Apply coherency filter on startup
            filtered_prompts = filter_coherency(user_prompts, state.bpm)
            bpm_prompts = get_bpm_prompts(state.bpm)
            await session.set_weighted_prompts(
                prompts=[
                    types.WeightedPrompt(text=t, weight=w)
                    for t, w in (filtered_prompts + bpm_prompts)
                ]
            )
            await session.set_music_generation_config(
                config=types.LiveMusicGenerationConfig(
                    bpm=state.bpm,
                    temperature=0.9,
                )
            )
            state.last_applied_bpm = state.bpm
            await session.play()
            logger.info("Lyria session.play() called. Buffering audio...")

            await asyncio.gather(
                receive_audio(session, state, audio_queue),
                apply_config_updates(session, state),
            )
    except Exception as e:
        logger.error(f"Failed to connect or maintain Lyria session: {e}")
        state.error = str(e)
        state.running = False
    finally:
        audio_queue.put(None)
