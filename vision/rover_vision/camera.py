"""Raspberry Pi camera wrapper (Picamera2 / libcamera)."""

import time

from . import config


def open_camera():
    """Create, configure and start the Pi camera, retrying on transient errors.

    A frame is captured before returning so that a camera which starts but
    never delivers frames (usually a loose ribbon cable) fails here with a
    clear message instead of hanging the navigation loop.
    """
    from picamera2 import Picamera2   # only available on the Pi

    last_error = None
    for attempt in range(1, config.CAMERA_STARTUP_RETRIES + 1):
        picam2 = None
        try:
            picam2 = Picamera2()
            picam2.configure(picam2.create_video_configuration(
                main={'size': (config.IMG_WIDTH, config.IMG_HEIGHT),
                      'format': config.CAMERA_FORMAT},
                raw={'size': (config.CAMERA_RAW_WIDTH, config.CAMERA_RAW_HEIGHT)},
                controls={'FrameRate': config.FRAMERATE},
                buffer_count=config.CAMERA_BUFFER_COUNT,
            ))
            picam2.start()
            picam2.capture_array()
            print(f'[camera] ready: {config.IMG_WIDTH}x{config.IMG_HEIGHT} '
                  f'{config.CAMERA_FORMAT}, raw {config.CAMERA_RAW_WIDTH}x'
                  f'{config.CAMERA_RAW_HEIGHT}')
            return picam2
        except Exception as exc:
            last_error = exc
            if picam2 is not None:
                for cleanup in (picam2.stop, picam2.close):
                    try:
                        cleanup()
                    except Exception:
                        pass
            print(f'[camera] open attempt {attempt}/{config.CAMERA_STARTUP_RETRIES} failed: {exc}')
            time.sleep(0.5)

    if last_error and 'resource busy' in str(last_error).lower():
        raise RuntimeError(
            'Camera is already in use. Stop any other run_rover.py, rpicam-hello '
            'or Python process holding the camera, then retry.'
        ) from last_error
    raise RuntimeError(
        'Camera started but no frame arrived. Reseat the ribbon cable at both '
        'ends (contacts facing the right way) and check the Pi power supply. '
        'Run `rpicam-hello --timeout 5000` to test the camera on its own.'
    ) from last_error


def capture_bgr_frame(picam2):
    """Grab the latest frame as an OpenCV-ready BGR array."""
    return picam2.capture_array('main')


def camera_metadata_summary(picam2):
    """One-line summary of the auto-exposure state, for periodic logging."""
    md = picam2.capture_metadata()
    exposure_us = md.get('ExposureTime')
    gain = md.get('AnalogueGain')
    lux = md.get('Lux')
    parts = []
    if exposure_us is not None:
        parts.append(f'exposure={exposure_us / 1000:.1f}ms')
    if gain is not None:
        parts.append(f'gain={gain:.2f}')
    if lux is not None:
        parts.append(f'lux={lux:.0f}')
    return ' '.join(parts) or 'no metadata'
