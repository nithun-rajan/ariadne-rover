"""Run the rover: Pi camera -> gate detection -> steering letters over UART.

    python run_rover.py              # full rover (UART + LEDs)
    python run_rover.py --no-rover   # vision + web stream only, no hardware outputs
    python run_rover.py --overlay    # draw detections on the web stream
"""

import argparse
import time

from rover_vision import config
from rover_vision.camera import camera_metadata_summary, capture_bgr_frame, open_camera
from rover_vision.link import LedPanel, NullLeds, NullLink, SerialLink
from rover_vision.navigator import GateNavigator
from rover_vision.overlay import draw_overlay
from rover_vision.pipeline import GatePipeline
from rover_vision.stream import FrameBuffer, StreamServer


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--no-rover', action='store_true',
                        help='disable UART and GPIO (bench testing the vision only)')
    parser.add_argument('--overlay', action='store_true',
                        help='annotate the web stream (costs some frame rate)')
    parser.add_argument('--port', type=int, default=config.STREAM_PORT,
                        help='web stream port (default: %(default)s)')
    parser.add_argument('--quiet', action='store_true', help='no per-frame log line')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.no_rover:
        print('[no-rover] UART and GPIO disabled')
        link, leds = NullLink(), NullLeds()
    else:
        link, leds = SerialLink(), LedPanel()

    frames = FrameBuffer()
    server = StreamServer(frames, port=args.port).start()
    print(f'[stream] {server.url}')

    picam2 = open_camera()
    pipeline = GatePipeline()
    navigator = GateNavigator()
    frame_count = 0

    try:
        while True:
            t0 = time.monotonic()
            frame_count += 1

            frame = capture_bgr_frame(picam2)
            result = pipeline.process(frame)
            letter, passed = navigator.update(result.gate)
            if passed:
                pipeline.tracker.reset()
                print(f'*** GATE {navigator.gates_passed} PASSED ***')

            leds.show(result.command)
            link.send(letter)

            if args.overlay:
                status = (f'TX:{letter}  gate #{navigator.gates_passed + 1}  '
                          f'[{navigator.state}]')
                frames.set(draw_overlay(frame, result.markers, result.gate,
                                        result.command, status))
            else:
                frames.set(frame)

            if frame_count % config.CAMERA_METADATA_LOG_INTERVAL == 0:
                print(f'[camera] {camera_metadata_summary(picam2)}')
            if not args.quiet:
                fps = 1.0 / max(time.monotonic() - t0, 1e-6)
                print(f'{fps:5.1f} fps | markers={len(result.markers)} | '
                      f'gate={result.gate_status} | cmd={result.command} | '
                      f'TX={letter} | gate#{navigator.gates_passed + 1} | {navigator.state}')
    except KeyboardInterrupt:
        print('\nStopping.')
    finally:
        picam2.stop()
        server.stop()
        leds.close()
        link.close()


if __name__ == '__main__':
    main()
