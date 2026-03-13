"""Unit tests for debug_output.write_debug_files."""
from __future__ import annotations

import pytest

from debug_output import write_debug_files


def test_write_debug_files_creates_png_and_log(five_colours_bgr, tmp_path) -> None:
    notes_vel = [(60, 80), (62, 90), (64, 70), (65, 100), (67, 85)]
    write_debug_files(str(tmp_path), five_colours_bgr, notes_vel, timestamp=1700000000)
    png_path = tmp_path / "1700000000.png"
    log_path = tmp_path / "1700000000.log"
    assert png_path.exists()
    assert log_path.exists()
    assert png_path.stat().st_size > 0
    text = log_path.read_text()
    assert "rank" in text and "colour" in text and "midi_note" in text and "velocity" in text
    lines = [l for l in text.strip().splitlines() if l]
    assert len(lines) >= 5


def test_write_debug_files_creates_frame_png_when_frame_provided(
    five_colours_bgr, synthetic_frame_bgr, tmp_path
) -> None:
    notes_vel = [(60, 80), (62, 90), (64, 70), (65, 100), (67, 85)]
    write_debug_files(
        str(tmp_path), five_colours_bgr, notes_vel, timestamp=1700000000, frame=synthetic_frame_bgr
    )
    frame_path = tmp_path / "1700000000-frame.png"
    assert frame_path.exists()
    assert frame_path.stat().st_size > 0
