"""
Colour analysis: extract the top 5 most prevalent colours from a frame using k-means.
"""
from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np

# Default max dimension for downscaling before k-means (keeps analysis fast)
DEFAULT_MAX_SIZE = 200


def get_top5_colours(
    frame: np.ndarray,
    max_size: int = DEFAULT_MAX_SIZE,
    k: int = 5,
) -> List[Tuple[int, int, int]]:
    """
    Return the 5 dominant BGR colours in the frame, ordered from most to least prevalent.

    - Downscales the frame so the longest side is at most max_size pixels.
    - Runs k-means with k=5 on pixel colours, then sorts clusters by size (largest first).
    - Returns a list of 5 (B, G, R) tuples in range 0-255.

    Args:
        frame: BGR image (H, W, 3), uint8.
        max_size: Max dimension for downscaling; use 0 to skip resize.
        k: Number of clusters (default 5).

    Returns:
        List of 5 (B, G, R) tuples, most prevalent first.
    """
    if frame is None or frame.size == 0:
        return [(0, 0, 0)] * k

    # Downscale to speed up k-means
    h, w = frame.shape[:2]
    if max_size > 0 and max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Flatten to (N, 3) BGR
    pixels = frame.reshape(-1, 3).astype(np.float32)

    # k-means: 5 clusters, 10 iterations, random centers
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS
    )
    centers = np.uint8(centers)  # (k, 3) BGR

    # Sort by cluster size (most pixels first)
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(-counts)[:k]  # descending

    result = []
    for i in order:
        b, g, r = centers[i]
        result.append((int(b), int(g), int(r)))

    return result
