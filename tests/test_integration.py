"""
Integration tests: run the full pipeline (frame → colours → MIDI) with fake frames and mock MIDI.
No real camera or MIDI hardware required.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from colours import get_top5_colours
from midi import colours_to_notes


def test_pipeline_fake_frames_to_mock_midi(synthetic_frame_bgr: np.ndarray) -> None:
    """One poll: frame → top 5 colours → notes → mock send_chord. No crashes."""
    mock_send = MagicMock()
    colours = get_top5_colours(synthetic_frame_bgr, max_size=100)
    assert len(colours) == 5
    notes_vel = colours_to_notes(colours, note_min=48, note_max=72)
    assert len(notes_vel) == 5
    mock_send(notes_vel)
    mock_send.assert_called_once()
    args = mock_send.call_args[0][0]
    assert len(args) == 5
    for note, vel in args:
        assert 48 <= note <= 72
        assert 1 <= vel <= 127


def test_pipeline_multiple_polls() -> None:
    """Simulate 3 polls: different synthetic frames, each produces 5 notes and can be 'sent'."""
    frames = [
        np.full((50, 50, 3), (255, 0, 0), dtype=np.uint8),
        np.full((50, 50, 3), (0, 255, 0), dtype=np.uint8),
        np.full((50, 50, 3), (0, 0, 255), dtype=np.uint8),
    ]
    sent = []
    for frame in frames:
        colours = get_top5_colours(frame, max_size=0)
        notes_vel = colours_to_notes(colours, note_min=36, note_max=84)
        sent.append(notes_vel)
    assert len(sent) == 3
    for chord in sent:
        assert len(chord) == 5
        for note, vel in chord:
            assert 36 <= note <= 127
            assert 1 <= vel <= 127
