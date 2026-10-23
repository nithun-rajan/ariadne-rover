"""Render synthetic gate markers for tests."""

import cv2
import numpy as np

from rover_vision import config


def marker_image(pattern, size=200, border_fraction=config.MARKER_BORDER_FRACTION):
    """A marker card: black border around a grid of black (1) / white (0) cells."""
    pattern = np.asarray(pattern)
    n = pattern.shape[0]
    img = np.zeros((size, size), np.uint8)
    border = int(round(size * border_fraction))
    cell = (size - 2 * border) / n
    for r in range(n):
        for c in range(n):
            if pattern[r, c] == 0:
                y0, y1 = int(border + r * cell), int(border + (r + 1) * cell)
                x0, x1 = int(border + c * cell), int(border + (c + 1) * cell)
                img[y0:y1, x0:x1] = 255
    return img


def place_marker(canvas, pattern, centre, side, angle_deg=0.0, tilt=0.0):
    """Paste a marker into a grayscale canvas with rotation and perspective.

    tilt > 0 shrinks the right edge, as if the card were turned away from
    the camera about its vertical axis.
    """
    src_img = marker_image(pattern)
    s = src_img.shape[0]
    src = np.float32([[0, 0], [s, 0], [s, s], [0, s]])

    half = side / 2
    shrink = half * tilt
    dst = np.float32([[-half, -half], [half, -half + shrink],
                      [half, half - shrink], [-half, half]])
    a = np.deg2rad(angle_deg)
    rot = np.float32([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    dst = dst @ rot.T + np.float32(centre)

    H = cv2.getPerspectiveTransform(src, dst)
    h, w = canvas.shape[:2]
    warped = cv2.warpPerspective(src_img, H, (w, h), borderValue=0)
    mask = cv2.warpPerspective(np.full_like(src_img, 255), H, (w, h), borderValue=0)
    canvas[mask > 127] = warped[mask > 127]
    return dst


def scene(markers, width=config.IMG_WIDTH, height=config.IMG_HEIGHT,
          background=200, blur=0, noise=0.0, seed=0):
    """Build a BGR frame containing the given markers.

    markers: list of dicts with keys pattern, centre, side and optionally
    angle_deg / tilt.
    """
    canvas = np.full((height, width), background, np.uint8)
    for m in markers:
        place_marker(canvas, m['pattern'], m['centre'], m['side'],
                     m.get('angle_deg', 0.0), m.get('tilt', 0.0))
    if blur:
        canvas = cv2.GaussianBlur(canvas, (0, 0), blur)
    if noise:
        rng = np.random.default_rng(seed)
        canvas = np.clip(canvas + rng.normal(0, noise, canvas.shape), 0, 255).astype(np.uint8)
    return cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
