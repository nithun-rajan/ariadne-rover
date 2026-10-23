"""Stage 1: find square marker candidates in a grayscale frame.

Adaptive thresholding responds to local contrast rather than absolute
brightness, so the black marker borders survive uneven indoor lighting. Every
contour is then filtered down to convex, roughly square quadrilaterals.
"""

import cv2
import numpy as np

from . import config
from .geometry import distance, order_corners, shoelace_area


def threshold_edges(gray):
    blur = cv2.GaussianBlur(gray, (config.BLUR_KERNEL_SIZE, config.BLUR_KERNEL_SIZE), 0)
    binary = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        config.ADAPTIVE_BLOCK_SIZE,
        config.ADAPTIVE_C,
    )
    # Close one-pixel gaps so each border forms a single closed contour.
    kernel = np.ones((3, 3), np.uint8)
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)


def square_from_contour(contour, min_area, max_area):
    """Return a candidate dict if the contour is a plausible marker, else None."""
    area = cv2.contourArea(contour)
    if not min_area <= area <= max_area:
        return None

    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, config.POLY_APPROX_EPSILON * perimeter, True)
    if len(approx) != 4 or not cv2.isContourConvex(approx):
        return None

    corners = order_corners(approx.reshape(4, 2))

    (_, _), (w, h), _ = cv2.minAreaRect(corners)
    if min(w, h) < config.MIN_MARKER_SIDE:
        return None
    if max(w, h) / min(w, h) > config.MAX_ASPECT_RATIO:
        return None

    sides = [distance(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    if max(sides) / (min(sides) + 1e-6) > config.MAX_SIDE_RATIO:
        return None

    centre = corners.mean(axis=0)
    return {
        'corners': corners,
        'center': (float(centre[0]), float(centre[1])),
        'area': float(shoelace_area(corners)),
    }


def find_squares(gray, min_area=config.MIN_MARKER_AREA, max_area=config.MAX_MARKER_AREA):
    """Detect square candidates.

    Returns a list of dicts with 'corners' (4x2, clockwise from top-left),
    'center' (x, y) and 'area' (px^2).
    """
    binary = threshold_edges(gray)
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    squares = []
    for contour in contours:
        candidate = square_from_contour(contour, min_area, max_area)
        if candidate is not None:
            squares.append(candidate)
    return squares
