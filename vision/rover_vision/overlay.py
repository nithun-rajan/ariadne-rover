"""Debug drawing shared by the rover stream and the webcam demo."""

import cv2

from . import config

GREEN = (0, 255, 0)
RED = (0, 0, 255)
GREY = (128, 128, 128)
YELLOW = (0, 255, 255)
AMBER = (0, 180, 255)
WHITE = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX

MARKER_COLOURS = {'left': GREEN, 'right': RED}
COMMAND_COLOURS = {
    'go': GREEN,
    'light_left': (0, 165, 255), 'strong_left': (0, 165, 255),
    'light_right': (255, 100, 100), 'strong_right': (255, 100, 100),
}


def draw_zones(vis):
    h, w = vis.shape[:2]
    left = int(config.STEER_ZONE_LEFT * w / config.IMG_WIDTH)
    right = int(config.STEER_ZONE_RIGHT * w / config.IMG_WIDTH)
    for x in (left // 2, left, right, right + (w - right) // 2):
        cv2.line(vis, (x, 0), (x, h), (60, 60, 60), 1)
    cv2.line(vis, (w // 2, 0), (w // 2, h), (40, 40, 40), 1)


def draw_markers(vis, markers):
    for m in markers:
        colour = MARKER_COLOURS.get(m['type'], GREY)
        cv2.polylines(vis, [m['corners'].astype(int).reshape(-1, 1, 2)], True, colour, 2)
        cx, cy = int(m['center'][0]), int(m['center'][1])
        cv2.circle(vis, (cx, cy), 4, colour, -1)
        cv2.putText(vis, f"{m['type']} d={m['match_error']}", (cx - 35, cy - 12),
                    FONT, 0.5, colour, 2)


def draw_gate(vis, gate):
    if gate is None:
        return
    colour = AMBER if gate.get('stale') else YELLOW
    left = tuple(int(v) for v in gate['left']['center'])
    right = tuple(int(v) for v in gate['right']['center'])
    centre = tuple(int(v) for v in gate['center'])
    cv2.line(vis, left, right, colour, 2)
    cv2.circle(vis, centre, 10, colour, -1)
    cv2.putText(vis, 'gate (held)' if gate.get('stale') else 'gate',
                (centre[0] + 14, centre[1] + 5), FONT, 0.5, colour, 1)


def draw_overlay(frame, markers, gate, command, status=None, zones=True):
    """Return a copy of frame annotated with markers, gate and command."""
    vis = frame.copy()
    if zones:
        draw_zones(vis)
    draw_markers(vis, markers)
    draw_gate(vis, gate)

    label = 'NO GATE' if command == 'stop' else command.upper().replace('_', ' ')
    cv2.putText(vis, label, (10, 35), FONT, 1.0, COMMAND_COLOURS.get(command, GREY), 3)
    if status:
        cv2.putText(vis, status, (10, 68), FONT, 0.6, WHITE, 2)
    return vis
