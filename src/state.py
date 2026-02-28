"""
Shared state between UI and music thread.
Single source of truth for BPM, prompts, and status.
"""

from typing import Optional


class MusicState:
    """Mutable state shared between Streamlit UI and Lyria music thread."""

    def __init__(self) -> None:
        self.bpm: int = 80
        self.prompts: list[tuple[str, float]] = []
        self.running: bool = False
        self.error: Optional[str] = None
        self.chunks_received: int = 0
        self.last_applied_bpm: Optional[int] = None
