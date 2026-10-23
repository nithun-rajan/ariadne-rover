"""Try the vision pipeline on a laptop webcam, no rover needed.

    python run_webcam.py                 # default camera
    python run_webcam.py --camera 1      # another camera index
    python run_webcam.py --video run.mp4 # a recorded video instead

Uses webcam_patterns.json from calibrate_patterns.py if present, otherwise
the Pi patterns in config.py. Press Q to quit.
"""

import argparse
import json
import os
import sys
import time

import cv2

from rover_vision import config
from rover_vision.markers import MarkerDetector
from rover_vision.navigator import GateNavigator
from rover_vision.overlay import draw_overlay
from rover_vision.pipeline import GatePipeline

HERE = os.path.dirname(os.path.abspath(__file__))


def load_patterns():
    path = os.path.join(HERE, config.WEBCAM_PATTERNS_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f), config.WEBCAM_PATTERNS_FILE
    return config.PATTERNS_PI, 'config.PATTERNS_PI'


def open_capture(args):
    if args.video:
        return cv2.VideoCapture(args.video)
    backend = cv2.CAP_AVFOUNDATION if sys.platform == 'darwin' else cv2.CAP_ANY
    cap = cv2.VideoCapture(args.camera, backend)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.IMG_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.IMG_HEIGHT)
    return cap


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--video', help='path to a video file to replay')
    args = parser.parse_args()

    patterns, source = load_patterns()
    print(f'Marker patterns from {source}. Press Q to quit.')

    cap = open_capture(args)
    if not cap.isOpened():
        sys.exit('Cannot open the camera. On macOS, allow camera access for your '
                 'terminal in System Settings > Privacy & Security > Camera.')

    pipeline = GatePipeline(detector=MarkerDetector(patterns))
    navigator = None

    try:
        while True:
            t0 = time.monotonic()
            ok, frame = cap.read()
            if not ok:
                break

            if navigator is None:
                navigator = GateNavigator(img_width=frame.shape[1])
            result = pipeline.process(frame)
            letter, passed = navigator.update(result.gate)
            if passed:
                pipeline.tracker.reset()

            fps = 1.0 / max(time.monotonic() - t0, 1e-6)
            status = f'{fps:4.1f} fps  TX:{letter}  [{navigator.state}]'
            cv2.imshow('Ariadne - webcam', draw_overlay(
                frame, result.markers, result.gate, result.command, status))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
