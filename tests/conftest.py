"""
Shared pytest fixtures: synthetic frame, mock VideoCapture, mock MIDI output.
"""
from __future__ import annotations

from typing import List, Tuple
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def synthetic_frame_bgr() -> np.ndarray:
    """A small BGR image (e.g. 80x60) with some colour variation for k-means."""
    h, w = 60, 80
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # Left third red, middle green, right third blue
    img[:, : w // 3] = [0, 0, 255]
    img[:, w // 3 : 2 * w // 3] = [0, 255, 0]
    img[:, 2 * w // 3 :] = [255, 0, 0]
    return img


@pytest.fixture
def five_colours_bgr() -> List[Tuple[int, int, int]]:
    """Five BGR colours (e.g. for MIDI mapping tests)."""
    return [
        (255, 0, 0),    # BGR red
        (0, 255, 0),    # BGR green
        (0, 0, 255),    # BGR blue
        (255, 255, 0), # BGR cyan
        (0, 255, 255), # BGR yellow
    ]


@pytest.fixture
def mock_video_capture(synthetic_frame_bgr: np.ndarray):
    """Mock cv2.VideoCapture that returns (True, synthetic_frame_bgr) on read()."""
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, synthetic_frame_bgr.copy())
    cap.release = MagicMock()
    return cap


@pytest.fixture
def mock_midi_output():
    """Mock MIDI output that records sent messages (list of message dicts or mido messages)."""
    sent = []
    port = MagicMock()
    def _send(msg):
        sent.append(msg)
    port.send = _send
    port.close = MagicMock()
    port.sent = sent  # so tests can read it
    return port
