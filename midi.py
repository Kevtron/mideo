"""
MIDI output: map colours to (note, velocity), send to physical/virtual port or append to file.
"""
from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import cv2
import mido
import numpy as np

# Scale definitions: semitones relative to root (0-11). Used to quantize note to nearest scale degree.
SCALE_SEMITONES = {
    "pentatonic": (0, 2, 4, 7, 9),           # C major pentatonic (C, D, E, G, A)
    "blues_pentatonic": (0, 3, 5, 7, 10),   # C minor/blues pentatonic (C, Eb, F, G, Bb)
    "ionian": (0, 2, 4, 5, 7, 9, 11),       # Major (C, D, E, F, G, A, B)
    "dorian": (0, 2, 3, 5, 7, 9, 10),       # (C, D, Eb, F, G, A, Bb)
    "phrygian": (0, 1, 3, 5, 7, 8, 10),     # (C, Db, Eb, F, G, Ab, Bb)
    "lydian": (0, 2, 4, 6, 7, 9, 11),       # (C, D, E, F#, G, A, B)
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),   # (C, D, E, F, G, A, Bb)
    "aeolian": (0, 2, 3, 5, 7, 8, 10),      # Natural minor (C, D, Eb, F, G, Ab, Bb)
    "locrian": (0, 1, 3, 5, 6, 8, 10),      # (C, Db, Eb, F, Gb, Ab, Bb)
}


def _bgr_to_hsv(b: int, g: int, r: int) -> Tuple[float, float, float]:
    """Convert BGR to HSV. OpenCV uses H in [0, 180], S/V in [0, 255]. Return H in [0, 360], S/V in [0, 255]."""
    bgr = np.array([[[b, g, r]]], dtype=np.uint8)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[0, 0]
    h_360 = h * 2.0  # 0-180 -> 0-360
    return (h_360, float(s), float(v))


def _quantize_to_scale(note: int, scale: str) -> int:
    """Quantize MIDI note to the nearest degree of the given scale (semitones relative to root)."""
    semitones = SCALE_SEMITONES.get(scale)
    if not semitones:
        return note
    octave = note // 12
    semitone = note % 12
    def dist(s: int) -> int:
        d = abs(semitone - s)
        return min(d, 12 - d)
    nearest = min(semitones, key=dist)
    candidate = octave * 12 + nearest
    if semitone > 6 and nearest == 0:
        candidate = (octave + 1) * 12
    return max(0, min(127, candidate))


def colours_to_notes(
    colours_bgr: List[Tuple[int, int, int]],
    note_min: int = 36,
    note_max: int = 84,
    scale: str = "chromatic",
) -> List[Tuple[int, int]]:
    """
    Map each BGR colour to (MIDI note, velocity). Hue -> pitch, Value -> velocity.

    Args:
        colours_bgr: List of (B, G, R) tuples.
        note_min: Minimum MIDI note (inclusive).
        note_max: Maximum MIDI note (inclusive).
        scale: "chromatic" or any key in SCALE_SEMITONES (e.g. pentatonic, blues_pentatonic, ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian).

    Returns:
        List of (note, velocity) with note in [note_min, note_max], velocity in [1, 127].
    """
    result = []
    for (b, g, r) in colours_bgr:
        h, s, v = _bgr_to_hsv(b, g, r)
        # Hue 0-360 -> note in [note_min, note_max]
        note_range = note_max - note_min + 1
        note = note_min + int((h / 360.0) * note_range) % note_range
        note = note_min + (note - note_min) % note_range
        note = max(note_min, min(note_max, note))
        if scale != "chromatic" and scale in SCALE_SEMITONES:
            note = _quantize_to_scale(note, scale)
            note = max(note_min, min(note_max, note))
        # Value 0-255 -> velocity 1-127
        velocity = 1 + int((v / 255.0) * 126)
        velocity = max(1, min(127, velocity))
        result.append((note, velocity))
    return result


class MIDIOutput(ABC):
    """Abstract MIDI output: send a chord and optionally release the previous one."""

    @abstractmethod
    def send_chord(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        """Send note-on for each (note, velocity). Call release_previous() first if needed."""
        pass

    @abstractmethod
    def release_previous(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        """Send note-off for the previous chord (so no stuck notes)."""
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def __enter__(self) -> MIDIOutput:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class MidiPortOutput(MIDIOutput):
    """Send MIDI to a physical or virtual port (e.g. DAW / VCV Rack via virtual port)."""

    def __init__(self, port_name: Optional[str] = None, virtual: bool = False):
        self._port_name = port_name or "video-midi"
        self._virtual = virtual
        self._port: Optional[mido.ports.BaseOutput] = None
        self._last_notes: List[Tuple[int, int]] = []

    def open(self) -> None:
        if self._virtual:
            self._port = mido.open_output(self._port_name, virtual=True)
        else:
            if self._port_name not in mido.get_output_names():
                raise ValueError(f"MIDI output port not found: {self._port_name!r}. Available: {mido.get_output_names()}")
            self._port = mido.open_output(self._port_name)
        self._last_notes = []

    def send_chord(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        self.release_previous(self._last_notes, channel)
        if self._port is None:
            return
        for note, vel in notes_velocities:
            self._port.send(mido.Message("note_on", note=note, velocity=vel, channel=channel))
        self._last_notes = list(notes_velocities)

    def release_previous(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        if self._port is None or not notes_velocities:
            return
        for note, _ in notes_velocities:
            self._port.send(mido.Message("note_off", note=note, velocity=0, channel=channel))

    def close(self) -> None:
        if self._port is not None:
            self.release_previous(self._last_notes)
            self._port.close()
            self._port = None
        self._last_notes = []


class MidiFileOutput(MIDIOutput):
    """Append colour -> MIDI mapping to a text file (tab-separated) each time send_chord is called."""

    def __init__(self, path: str):
        self._path = path
        self._file = None

    def open(self) -> None:
        self._file = open(self._path, "a", newline="")

    def send_chord(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        # No note_on; we only log. Caller can pass colours for the log line.
        pass

    def release_previous(self, notes_velocities: List[Tuple[int, int]], channel: int = 0) -> None:
        pass

    def append_log(
        self,
        timestamp: int,
        colours_bgr: List[Tuple[int, int, int]],
        notes_velocities: List[Tuple[int, int]],
    ) -> None:
        """Append one block: timestamp and rows rank, colour (hex), midi_note, velocity."""
        if self._file is None:
            self._file = open(self._path, "a", newline="")
        w = csv.writer(self._file, delimiter="\t")
        w.writerow(["rank", "colour", "midi_note", "velocity"])
        for rank, ((b, g, r), (note, vel)) in enumerate(zip(colours_bgr, notes_velocities), start=1):
            hex_colour = "#{:02x}{:02x}{:02x}".format(r, g, b)
            w.writerow([rank, hex_colour, note, vel])
        self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None


def get_output_names() -> List[str]:
    """Return list of available MIDI output port names (for interactive selection)."""
    return list(mido.get_output_names())
