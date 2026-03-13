"""
Camera feed module: open USB or built-in camera by index or name, expose frames via read().
"""
from __future__ import annotations

import contextlib
from typing import Generator, List, Optional, Tuple

import cv2
import numpy as np


def list_devices(max_index: int = 10) -> List[Tuple[int, str]]:
    """
    Enumerate available camera devices. Tries indices 0..max_index-1 and returns
    those that open successfully. Display name is "Camera {index}" (backend may not expose real names).
    """
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append((i, f"Camera {i}"))
            cap.release()
    return available


def _resolve_device(device_index: Optional[int], device_name: Optional[str]) -> int:
    """Resolve device_index or device_name to a concrete index. Default 0."""
    if device_index is not None:
        return device_index
    if device_name is not None:
        devices = list_devices()
        for idx, name in devices:
            if device_name.strip().lower() in name.lower():
                return idx
        # Try matching "Camera 0" style
        try:
            return int(device_name.strip().split()[-1])
        except (ValueError, IndexError):
            pass
    return 0


class CameraFeed:
    """
    Headless camera feed: opens a camera by index or name, provides read() and context manager.
    Supports both USB and built-in (e.g. MacBook FaceTime) cameras.
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        device_name: Optional[str] = None,
    ):
        self._index = _resolve_device(device_index, device_name)
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """Open the camera. Returns True if successful."""
        self._cap = cv2.VideoCapture(self._index)
        return self._cap.isOpened()

    def release(self) -> None:
        """Release the camera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read one frame. Returns (success, frame). Frame is BGR numpy array or None if failed.
        """
        if self._cap is None or not self._cap.isOpened():
            return False, None
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, None
        return True, frame

    def frames(self) -> Generator[Tuple[bool, Optional[np.ndarray]], None, None]:
        """Generator that yields (ret, frame) until release or failure."""
        try:
            while True:
                ret, frame = self.read()
                if not ret:
                    break
                yield ret, frame
        finally:
            self.release()

    def __enter__(self) -> CameraFeed:
        if not self.open():
            raise RuntimeError(f"Could not open camera at index {self._index}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
        return None


@contextlib.contextmanager
def open_camera(
    device_index: Optional[int] = None,
    device_name: Optional[str] = None,
) -> Generator[CameraFeed, None, None]:
    """Context manager: yield a CameraFeed and release on exit."""
    feed = CameraFeed(device_index=device_index, device_name=device_name)
    try:
        if not feed.open():
            raise RuntimeError(f"Could not open camera at index {feed._index}")
        yield feed
    finally:
        feed.release()
