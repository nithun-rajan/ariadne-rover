import numpy as np
import pytest

from rover_vision.geometry import angle_from_horizontal, order_corners, shoelace_area


def test_shoelace_area():
    assert shoelace_area([[0, 0], [4, 0], [4, 3], [0, 3]]) == pytest.approx(12.0)
    assert shoelace_area([[0, 0], [0, 3], [4, 3], [4, 0]]) == pytest.approx(12.0)


def test_angle_from_horizontal():
    assert angle_from_horizontal((0, 0), (10, 0)) == 0.0
    assert angle_from_horizontal((0, 0), (10, 10)) == pytest.approx(45.0)
    assert angle_from_horizontal((5, 0), (5, 10)) == 90.0


@pytest.mark.parametrize('angle', [0, 10, 44, 45, 46, 90, 135, 200])
def test_order_corners_is_a_valid_clockwise_quad(angle):
    a = np.deg2rad(angle)
    square = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], float)
    rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    pts = square @ rot.T * 50 + 100
    shuffled = pts[[2, 0, 3, 1]]

    ordered = order_corners(shuffled)

    assert len({tuple(p) for p in ordered.round(3)}) == 4     # no repeated corner
    # Positive signed area in image coordinates (y down) means clockwise on screen.
    x, y = ordered[:, 0], ordered[:, 1]
    signed = 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))
    assert signed > 0
    assert np.argmin(ordered.sum(axis=1)) == 0
