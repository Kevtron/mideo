"""Unit tests for camera module (mocked VideoCapture)."""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from camera import CameraFeed, list_devices, open_camera


def test_list_devices_mocked() -> None:
    """Without a real camera, list_devices may return [] or indices that open. We just check it returns a list of (int, str)."""
    devices = list_devices(max_index=3)
    assert isinstance(devices, list)
    for item in devices:
        assert isinstance(item, (list, tuple)) and len(item) == 2
        idx, name = item
        assert isinstance(idx, int)
        assert isinstance(name, str)


def test_camera_feed_resolve_index() -> None:
    """CameraFeed with device_index opens that index."""
    feed = CameraFeed(device_index=0)
    assert feed._index == 0


def test_camera_feed_read_mocked(mock_video_capture, synthetic_frame_bgr) -> None:
    """When VideoCapture is mocked, read() returns the mock frame."""
    with patch("camera.cv2.VideoCapture", return_value=mock_video_capture):
        feed = CameraFeed(device_index=0)
        feed.open()
        ret, frame = feed.read()
        assert ret is True
        assert frame is not None
        assert frame.shape == synthetic_frame_bgr.shape
        feed.release()


def test_camera_feed_context_manager_releases(mock_video_capture) -> None:
    with patch("camera.cv2.VideoCapture", return_value=mock_video_capture):
        with CameraFeed(device_index=0) as feed:
            pass
        mock_video_capture.release.assert_called()
