# music.py
import pygame
import numpy as np

SAMPLE_RATE = 44100

def make_tone(freq, duration, volume=0.3, wave="square"):
    """Generate a numpy audio buffer for a single tone."""
    frames = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, frames, endpoint=False)

    if wave == "square":
        raw = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        raw = np.sin(2 * np.pi * freq * t)

    # Simple envelope: quick attack, gentle fade at end
    envelope = np.ones(frames)
    fade = int(frames * 0.15)
    envelope[-fade:] = np.linspace(1, 0, fade)
    envelope[:int(frames * 0.02)] = np.linspace(0, 1, int(frames * 0.02))

    samples = (raw * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples])
    return stereo

def make_silence(duration):
    frames = int(SAMPLE_RATE * duration)
    return np.zeros((frames, 2), dtype=np.int16)

# Note frequencies
NOTE = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63,
    "F4": 349.23, "G4": 392.00, "A4": 440.00,
    "B4": 493.88, "C5": 523.25, "D5": 587.33,
    "E5": 659.25, "G5": 783.99,
    "REST": 0
}

# "If You're Happy and You Know It"
# (note, duration_in_beats)  — beat = 0.22s at this tempo
BEAT = 0.22
SONG = [
    ("G4",1),("G4",1),("G4",1),("E4",1.5),("G4",0.5),
    ("G4",1),("E4",1.5),("G4",0.5),("G4",1),("G4",1),
    ("B4",1),("B4",1),("A4",1),("G4",1),("A4",1),("G4",2),
    ("REST",0.5),
    ("D5",1),("D5",1),("D5",1),("D5",1.5),("B4",0.5),
    ("C5",1),("C5",1),("C5",1),("C5",1.5),("A4",0.5),
    ("G4",1),("G4",0.5),("G4",0.5),("B4",1),("B4",0.5),("B4",0.5),
    ("A4",1),("G4",1),("A4",1),("G4",2),
]

def build_song():
    """Stitch all notes into one audio buffer and return a Sound."""
    parts = []
    for note, beats in SONG:
        dur = beats * BEAT
        if note == "REST":
            parts.append(make_silence(dur))
        else:
            parts.append(make_tone(NOTE[note], dur))
        parts.append(make_silence(0.02))  # tiny gap between notes

    full = np.concatenate(parts, axis=0)
    # Ensure C-contiguous for pygame
    sound_array = np.ascontiguousarray(full)
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def init_music():
    """Call once after pygame.init(). Returns a Sound object."""
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
    return build_song()