"""
Debug output: write timestamped PNG (5 colour bars), captured frame, and tab-separated .log per poll.
"""
from __future__ import annotations

import os
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np

BAR_HEIGHT = 60
BAR_WIDTH = 400


def write_debug_files(
    output_dir: str,
    colours_bgr: List[Tuple[int, int, int]],
    notes_velocities: List[Tuple[int, int]],
    timestamp: Optional[int] = None,
    frame: Optional[np.ndarray] = None,
) -> None:
    """
    Write {timestamp}.png (5 horizontal bars), {timestamp}-frame.png (captured frame if provided),
    and {timestamp}.log (tab-separated: rank, colour, midi_note, velocity).
    Uses current Unix time if timestamp is None.
    """
    ts = timestamp if timestamp is not None else int(time.time())
    os.makedirs(output_dir, exist_ok=True)

    # Captured frame (raw camera image)
    if frame is not None and frame.size > 0:
        frame_path = os.path.join(output_dir, f"{ts}-frame.png")
        cv2.imwrite(frame_path, frame)

    # PNG: 5 horizontal bars
    img = np.zeros((BAR_HEIGHT * 5, BAR_WIDTH, 3), dtype=np.uint8)
    for i, (b, g, r) in enumerate(colours_bgr[:5]):
        img[i * BAR_HEIGHT : (i + 1) * BAR_HEIGHT, :] = (b, g, r)
    png_path = os.path.join(output_dir, f"{ts}.png")
    cv2.imwrite(png_path, img)

    # LOG: tab-separated
    log_path = os.path.join(output_dir, f"{ts}.log")
    with open(log_path, "w", newline="") as f:
        import csv
        w = csv.writer(f, delimiter="\t")
        w.writerow(["rank", "colour", "midi_note", "velocity"])
        for rank, ((b, g, r), (note, vel)) in enumerate(
            zip(colours_bgr[:5], notes_velocities[:5]), start=1
        ):
            hex_colour = "#{:02x}{:02x}{:02x}".format(r, g, b)
            w.writerow([rank, hex_colour, note, vel])
