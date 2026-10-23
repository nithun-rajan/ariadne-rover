"""Small 2D geometry helpers used by marker detection and gate pairing."""

import math

import numpy as np


def shoelace_area(corners):
    """Area of a simple polygon from its ordered vertices (shoelace formula)."""
    pts = np.asarray(corners, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))


def distance(p1, p2):
    """Euclidean distance between two points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def angle_from_horizontal(p1, p2):
    """Angle of the line p1-p2 from the image x-axis, in degrees (0-90)."""
    dx = abs(p2[0] - p1[0])
    dy = abs(p2[1] - p1[1])
    if dx == 0:
        return 90.0
    return math.degrees(math.atan(dy / dx))


def midpoint(p1, p2):
    return [(p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0]


def order_corners(corners):
    """Order 4 points clockwise (on screen), starting nearest the top-left.

    Points are sorted by angle around their centroid, which gives a valid,
    non-self-intersecting order at any rotation. (The common x+y / y-x trick
    picks the same point twice when a square is rotated near 45 degrees.)
    """
    pts = np.asarray(corners, dtype=np.float32).reshape(4, 2)
    centre = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0])
    pts = pts[np.argsort(angles)]
    start = int(np.argmin(pts.sum(axis=1)))
    return np.roll(pts, -start, axis=0)
