"""Unit tests for midi.colours_to_notes and output classes (no real port)."""
from __future__ import annotations

import pytest

from midi import MidiFileOutput, colours_to_notes


def test_colours_to_notes_returns_five(five_colours_bgr) -> None:
    result = colours_to_notes(five_colours_bgr, note_min=36, note_max=84)
    assert len(result) == 5
    for note, vel in result:
        assert 36 <= note <= 84
        assert 1 <= vel <= 127


def test_colours_to_notes_velocity_in_range(five_colours_bgr) -> None:
    result = colours_to_notes(five_colours_bgr, note_min=48, note_max=72)
    for note, vel in result:
        assert 48 <= note <= 72
        assert 1 <= vel <= 127


def test_pentatonic_quantizes(five_colours_bgr) -> None:
    chromatic = colours_to_notes(five_colours_bgr, scale="chromatic")
    pentatonic = colours_to_notes(five_colours_bgr, scale="pentatonic")
    assert len(pentatonic) == 5
    # Pentatonic notes should be in C major pentatonic (0,2,4,7,9 mod 12)
    semitones = (0, 2, 4, 7, 9)
    for note, _ in pentatonic:
        assert (note % 12) in semitones


def test_midi_file_output_append_log(five_colours_bgr, tmp_path) -> None:
    path = tmp_path / "out.log"
    out = MidiFileOutput(str(path))
    out.open()
    notes_vel = colours_to_notes(five_colours_bgr, note_min=60, note_max=72)
    out.append_log(12345, five_colours_bgr, notes_vel)
    out.close()
    text = path.read_text()
    assert "rank" in text and "midi_note" in text and "velocity" in text
    assert "12345" not in text  # we don't write timestamp in the rows, but we could
    lines = [l for l in text.strip().splitlines() if l]
    assert len(lines) >= 5  # header + 5 data rows
