import itertools

import numpy as np
import pytest

from rover_vision import config
from rover_vision.markers import MarkerDetector, classify_grid, extract_grid, warp_to_patch
from tests.synthetic import marker_image, scene

LEFT = config.PATTERNS_PI['left']
RIGHT = config.PATTERNS_PI['right']


def test_patterns_are_separable_in_every_rotation():
    # The Hamming tolerance is only safe if the two patterns stay far apart
    # whichever way round the cards are mounted.
    left, right = np.array(LEFT), np.array(RIGHT)
    closest = min(np.count_nonzero(np.rot90(left, k) != right) for k in range(4))
    assert closest > 2 * config.MAX_HAMMING_DISTANCE


@pytest.mark.parametrize('name', ['left', 'right'])
@pytest.mark.parametrize('turns', range(4))
def test_classify_any_rotation(name, turns):
    grid = np.rot90(np.array(config.PATTERNS_PI[name]), turns)
    marker_type, error, _ = classify_grid(grid, config.PATTERNS_PI)
    assert (marker_type, error) == (name, 0)


def test_classify_tolerates_flipped_cells_and_rejects_noise():
    grid = np.array(LEFT)
    grid[0, 0] ^= 1
    grid[3, 3] ^= 1
    assert classify_grid(grid, config.PATTERNS_PI)[:2] == ('left', 2)

    assert classify_grid(np.ones((4, 4), int), config.PATTERNS_PI)[0] == 'unknown'


def test_extract_grid_reads_a_rectified_marker():
    img = marker_image(RIGHT, size=200)
    corners = np.float32([[0, 0], [199, 0], [199, 199], [0, 199]])
    assert extract_grid(warp_to_patch(img, corners)).tolist() == RIGHT


CONDITIONS = {
    'frontal': {},
    'rotated_30': {'angle_deg': 30},
    'rotated_45': {'angle_deg': 45},
    'upside_down': {'angle_deg': 180},
    'tilted': {'tilt': 0.2},
    'tilted_rotated': {'tilt': 0.15, 'angle_deg': -20},
}
IMAGE_QUALITY = {
    'clean': {},
    'blurred': {'blur': 1.5},
    'noisy': {'noise': 12.0},
    'dim': {'background': 120},
}


@pytest.mark.parametrize('pose,quality',
                         itertools.product(CONDITIONS, IMAGE_QUALITY))
def test_detects_and_identifies_gate_markers(pose, quality):
    frame = scene([
        {'pattern': LEFT, 'centre': (400, 360), 'side': 120, **CONDITIONS[pose]},
        {'pattern': RIGHT, 'centre': (880, 360), 'side': 120, **CONDITIONS[pose]},
    ], **IMAGE_QUALITY[quality])

    markers = MarkerDetector().detect(frame, include_unknown=False)

    found = sorted((m['type'], round(m['center'][0] / 10)) for m in markers)
    assert found == [('left', 40), ('right', 88)]


@pytest.mark.parametrize('side', [45, 80, 160, 210])
def test_detects_across_distances(side):
    frame = scene([{'pattern': LEFT, 'centre': (640, 360), 'side': side}])
    markers = MarkerDetector().detect(frame, include_unknown=False)
    assert [m['type'] for m in markers] == ['left']


def test_one_detection_per_physical_marker():
    # A thick border produces both an outer and an inner contour.
    frame = scene([{'pattern': LEFT, 'centre': (640, 360), 'side': 180}])
    assert len(MarkerDetector().detect(frame)) == 1


def test_ignores_plain_squares():
    frame = scene([{'pattern': np.ones((4, 4), int), 'centre': (640, 360), 'side': 120}])
    assert MarkerDetector().detect(frame, include_unknown=False) == []


def test_custom_patterns():
    patterns = {'left': RIGHT, 'right': LEFT}   # swapped labels
    frame = scene([{'pattern': LEFT, 'centre': (640, 360), 'side': 120}])
    markers = MarkerDetector(patterns).detect(frame, include_unknown=False)
    assert [m['type'] for m in markers] == ['right']
