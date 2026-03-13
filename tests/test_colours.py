"""Unit tests for colours.get_top5_colours."""
from __future__ import annotations

import numpy as np
import pytest

from colours import get_top5_colours


def test_returns_five_colours(synthetic_frame_bgr: np.ndarray) -> None:
    result = get_top5_colours(synthetic_frame_bgr, max_size=0)
    assert len(result) == 5
    for item in result:
        assert len(item) == 3
        b, g, r = item
        assert 0 <= b <= 255 and 0 <= g <= 255 and 0 <= r <= 255


def test_order_by_prevalence(synthetic_frame_bgr: np.ndarray) -> None:
    # Frame has three dominant regions (R, G, B); k=5 still returns 5 centres sorted by cluster size
    result = get_top5_colours(synthetic_frame_bgr, max_size=0)
    assert len(result) == 5
    # All should be valid BGR
    for (b, g, r) in result:
        assert isinstance(b, (int, np.integer))
        assert isinstance(g, (int, np.integer))
        assert isinstance(r, (int, np.integer))


def test_empty_frame_returns_five_zeros() -> None:
    result = get_top5_colours(np.array([]), max_size=0)
    assert result == [(0, 0, 0)] * 5


def test_small_solid_frame() -> None:
    img = np.full((10, 10, 3), (100, 150, 200), dtype=np.uint8)  # BGR
    result = get_top5_colours(img, max_size=0)
    assert len(result) == 5
    # At least one cluster centre should be near the solid colour
    near = any(
        all(abs(c - t) < 30 for c, t in zip(item, (100, 150, 200)))
        for item in result
    )
    assert near
