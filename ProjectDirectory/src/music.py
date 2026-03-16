"""
music.py
========
Synthesised celebration music — no external audio files needed.
Generates "If You're Happy and You Know It" as a chiptune using numpy.

Public API
----------
init_music()        — call once after pygame.init()
play_celebration()  — start looping the song
stop_celebration()  — stop it
"""

import math
import pygame

# ── Note table & song sequence ────────────────────────────────────────────────

_SAMPLE_RATE = 44100

_NOTES = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25,
    "REST": 0,
}

_BEAT = 0.21   # seconds per beat

_SONG = [
    ("G4", 1), ("G4", 1), ("G4", 1), ("E4", 1.5), ("G4", 0.5),
    ("G4", 1), ("E4", 1.5), ("G4", 0.5), ("G4", 1), ("G4", 1),
    ("B4", 1), ("B4", 1), ("A4", 1), ("G4", 1), ("A4", 1), ("G4", 2),
    ("REST", 0.5),
    ("D5", 1), ("D5", 1), ("D5", 1), ("D5", 1.5), ("B4", 0.5),
    ("C5", 1), ("C5", 1), ("C5", 1), ("C5", 1.5), ("A4", 0.5),
    ("G4", 1), ("G4", 0.5), ("G4", 0.5),
    ("B4", 1), ("B4", 0.5), ("B4", 0.5),
    ("A4", 1), ("G4", 1), ("A4", 1), ("G4", 2),
]

# ── Module-level sound object ─────────────────────────────────────────────────

_sound = None   # pygame.Sound or None if numpy unavailable


# ── Public functions ──────────────────────────────────────────────────────────

def init_music() -> None:
    """Initialise the mixer and synthesise the song.  Call once at startup."""
    global _sound
    try:
        import numpy as np
        pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=2, buffer=512)
        parts = []
        for note, beats in _SONG:
            dur = beats * _BEAT
            if note == "REST":
                parts.append(_silence(dur))
            else:
                parts.append(_tone(_NOTES[note], dur))
            parts.append(_silence(0.02))   # tiny gap between notes
        full   = np.concatenate(parts, axis=0)
        _sound = pygame.sndarray.make_sound(np.ascontiguousarray(full))
    except Exception:
        _sound = None   # numpy missing or mixer unavailable — silent mode


def play_celebration() -> None:
    """Start the celebration song looping."""
    if _sound:
        _sound.play(loops=-1)


def stop_celebration() -> None:
    """Stop the celebration song."""
    if _sound:
        _sound.stop()


# ── Internal synthesis helpers ────────────────────────────────────────────────

def _tone(freq: float, duration: float, volume: float = 0.28):
    import numpy as np
    frames  = int(_SAMPLE_RATE * duration)
    t       = np.arange(frames) * (freq * 2 * math.pi / _SAMPLE_RATE)
    raw     = np.sign(np.sin(t))                  # square wave
    # Envelope: short attack + fade-out tail
    env     = np.ones(frames, dtype=np.float32)
    fade    = max(1, int(frames * 0.15))
    attack  = max(1, int(frames * 0.02))
    env[-fade:]   = np.linspace(1, 0, fade)
    env[:attack]  = np.linspace(0, 1, attack)
    samples = (raw * env * volume * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([samples, samples]))


def _silence(duration: float):
    import numpy as np
    return np.zeros((int(_SAMPLE_RATE * duration), 2), dtype=np.int16)
