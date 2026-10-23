"""Stage 2: decode each square candidate and classify it as a gate marker.

square contour -> perspective warp -> 4x4 binary grid -> nearest pattern
(Hamming distance over all four rotations) -> 'left' / 'right' / 'unknown'
"""

import cv2
import numpy as np

from . import config
from .squares import find_squares


def warp_to_patch(image, corners, size=config.MARKER_PATCH_SIZE):
    """Rectify the quadrilateral into a flat size x size grayscale patch."""
    dst = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
                   dtype=np.float32)
    H = cv2.getPerspectiveTransform(np.asarray(corners, dtype=np.float32), dst)
    patch = cv2.warpPerspective(image, H, (size, size))
    if patch.ndim == 3:
        patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    return patch


def extract_grid(patch, grid_size=4, border_fraction=config.MARKER_BORDER_FRACTION):
    """Read the inner grid_size x grid_size cells of a rectified marker.

    Otsu picks the black/white threshold per marker, so the read adapts to
    exposure. Each cell is sampled over its central half to stay clear of
    blurred cell edges. Returns an int array, 1 = black, 0 = white.
    """
    _, binary = cv2.threshold(patch, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    size = patch.shape[0]
    border = int(round(size * border_fraction))
    inner = binary[border:size - border, border:size - border]
    cell = inner.shape[0] / grid_size
    margin = cell / 4

    grid = np.zeros((grid_size, grid_size), dtype=int)
    for row in range(grid_size):
        for col in range(grid_size):
            y0, y1 = int(row * cell + margin), int((row + 1) * cell - margin)
            x0, x1 = int(col * cell + margin), int((col + 1) * cell - margin)
            grid[row, col] = 1 if inner[y0:y1, x0:x1].mean() < 127 else 0
    return grid


def hamming_distance(a, b):
    return int(np.count_nonzero(np.asarray(a) != np.asarray(b)))


def classify_grid(grid, patterns, max_hamming=config.MAX_HAMMING_DISTANCE):
    """Match a grid against every pattern in all four rotations.

    Returns (marker_type, error, rotation) where rotation is the number of
    90-degree clockwise turns applied to the grid for the best match.
    """
    best = ('unknown', grid.size + 1, 0)
    rotated = np.asarray(grid)
    for rotation in range(4):
        for name, pattern in patterns.items():
            error = hamming_distance(rotated, pattern)
            if error < best[1]:
                best = (name, error, rotation)
        rotated = np.rot90(rotated, k=-1)

    if best[1] > max_hamming:
        return 'unknown', best[1], best[2]
    return best


def _scale(marker):
    return float(np.sqrt(max(marker['area'], 1.0)))


def _rank(marker):
    # Known beats unknown, a closer match beats a worse one, and the larger
    # (outer) contour beats an inner duplicate of the same border.
    return (marker['type'] == 'unknown', marker['match_error'], -marker['area'])


def suppress_duplicates(markers, center_fraction=config.DUPLICATE_CENTER_FRACTION):
    """Keep one detection per physical marker."""
    kept = []
    for marker in sorted(markers, key=_rank):
        mx, my = marker['center']
        duplicate = any(
            np.hypot(mx - k['center'][0], my - k['center'][1])
            < center_fraction * max(_scale(marker), _scale(k))
            for k in kept
        )
        if not duplicate:
            kept.append(marker)
    return kept


class MarkerDetector:
    """Find and identify gate markers in camera frames."""

    def __init__(self, patterns=None, max_hamming=config.MAX_HAMMING_DISTANCE,
                 min_area=config.MIN_MARKER_AREA, max_area=config.MAX_MARKER_AREA):
        self.patterns = {name: np.asarray(p, dtype=int)
                         for name, p in (patterns or config.PATTERNS_PI).items()}
        sizes = {p.shape for p in self.patterns.values()}
        if len(sizes) != 1 or next(iter(sizes))[0] != next(iter(sizes))[1]:
            raise ValueError('all marker patterns must be square and the same size')
        self.grid_size = next(iter(sizes))[0]
        self.max_hamming = max_hamming
        self.min_area = min_area
        self.max_area = max_area

    def decode(self, image, corners):
        """Return (grid, marker_type, error, rotation) for one quadrilateral."""
        grid = extract_grid(warp_to_patch(image, corners), self.grid_size)
        marker_type, error, rotation = classify_grid(grid, self.patterns, self.max_hamming)
        return grid, marker_type, error, rotation

    def detect(self, frame, gray=None, include_unknown=True):
        """Detect markers in a BGR (or grayscale) frame.

        Each marker dict has 'corners', 'center', 'area', 'type', plus the
        debug fields 'grid', 'match_error' and 'rotation'.
        """
        if gray is None:
            gray = frame if frame.ndim == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        markers = []
        for candidate in find_squares(gray, self.min_area, self.max_area):
            grid, marker_type, error, rotation = self.decode(gray, candidate['corners'])
            if marker_type == 'unknown' and not include_unknown:
                continue
            markers.append({
                **candidate,
                'type': marker_type,
                'grid': grid,
                'match_error': error,
                'rotation': rotation,
            })
        return suppress_duplicates(markers)
