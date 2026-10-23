"""Capture the left/right marker grids with a webcam.

Hold each printed marker in front of the camera when prompted and press
SPACE (or Enter) to capture, ESC to retry. The grids are written to
webcam_patterns.json, which run_webcam.py loads automatically. To use them on
the rover, copy them into PATTERNS_PI in rover_vision/config.py.
"""

import json
import os
import sys

import cv2

from rover_vision import config
from rover_vision.markers import extract_grid, warp_to_patch
from rover_vision.squares import find_squares

HERE = os.path.dirname(os.path.abspath(__file__))


def capture_grid(cap, label):
    """Live preview of the largest square; returns its grid or None on ESC."""
    while True:
        ok, frame = cap.read()
        if not ok:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        squares = find_squares(gray)
        vis = frame.copy()
        grid = None

        if squares:
            best = max(squares, key=lambda s: s['area'])
            grid = extract_grid(warp_to_patch(gray, best['corners']))
            cv2.polylines(vis, [best['corners'].astype(int).reshape(-1, 1, 2)], True, (0, 255, 0), 2)
            for i, row in enumerate(grid):
                cv2.putText(vis, str(row.tolist()), (10, vis.shape[0] - 25 * (len(grid) - i)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            prompt, colour = f'{label}: SPACE to capture', (0, 255, 0)
        else:
            prompt, colour = f'{label}: no marker in view', (0, 0, 255)

        cv2.putText(vis, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, colour, 2)
        cv2.imshow('Calibrate markers', vis)

        key = cv2.waitKey(30) & 0xFF
        if key in (ord(' '), 13) and grid is not None:
            return grid.tolist()
        if key == 27:
            return None


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit('Cannot open the camera.')

    patterns = {}
    try:
        for label in ('left', 'right'):
            while label not in patterns:
                print(f'\nShow the {label.upper()} marker.')
                grid = capture_grid(cap, label)
                if grid is None:
                    print('  cancelled, try again')
                    continue
                for row in grid:
                    print('   ', row)
                if input('  Keep this grid? [y/n] ').strip().lower() == 'y':
                    patterns[label] = grid
    finally:
        cap.release()
        cv2.destroyAllWindows()

    path = os.path.join(HERE, config.WEBCAM_PATTERNS_FILE)
    with open(path, 'w') as f:
        json.dump(patterns, f, indent=2)
    print(f'\nSaved {path}')


if __name__ == '__main__':
    main()
