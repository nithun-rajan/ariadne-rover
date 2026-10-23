# Vision

Python/OpenCV pipeline that runs on the rover's Raspberry Pi and turns each
camera frame into a steering letter for the motor controller.

## Setup

**Laptop (demo and tests):**

```bash
cd vision
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest                  # synthetic-image test suite
python run_webcam.py    # live demo, press Q to quit
```

**Raspberry Pi** (Raspberry Pi OS Bookworm; Picamera2 ships with the OS):

```bash
sudo apt install -y python3-picamera2 python3-opencv python3-rpi.gpio python3-serial
cd vision
python run_rover.py
```

Enable the hardware UART (`sudo raspi-config` → Interface Options → Serial Port:
login shell **no**, hardware **yes**) so `/dev/ttyAMA0` is free for the Pico link.

## Entry points

| Script | Purpose |
|---|---|
| `run_rover.py` | On the rover: camera → UART letters + indicator LEDs + MJPEG stream. `--no-rover` disables UART/GPIO, `--overlay` draws detections on the stream. |
| `run_webcam.py` | Whole pipeline on a laptop webcam (`--camera N`) or a recorded video (`--video file.mp4`). |
| `calibrate_patterns.py` | Read the grids off your printed cards with a webcam; saves `webcam_patterns.json`, which `run_webcam.py` picks up. |

While `run_rover.py` is running, open the printed URL (e.g.
`http://raspberrypi.local:8080`) in a browser to watch the camera.

## Markers

Each card is a black square border (20% of the side on each edge) around a
4×4 grid of black/white cells. The grids are in `rover_vision/config.py`
(`PATTERNS_PI`, 1 = black). They are matched in all four rotations, so a card
can be mounted any way up. The two patterns differ in at least 8 of 16 cells in
every rotation (checked by the tests), so tolerating 2 misread cells is safe.

## Tuning

All knobs live in [`rover_vision/config.py`](rover_vision/config.py). The ones that matter most:

| Setting | Default | Effect |
|---|---|---|
| `MAX_HAMMING_DISTANCE` | 2 | Misread cells tolerated per card. Higher = more robust to blur, more false matches. |
| `MIN_MARKER_AREA` / `MAX_MARKER_AREA` | 1000 / 50000 px² | Detection range: small = far away, large = close. |
| `AREA_MATCH_THRESHOLD` | 0.35 | How different in size the two cards of a gate may look. |
| `GATE_SMOOTHING_ALPHA` | 0.35 | Lower = steadier, higher = more responsive steering. |
| `GATE_MEMORY_FRAMES` | 5 | Frames a gate is held after it is lost. |
| `GATE_ABSENT_THRESHOLD` / `COOLDOWN_FRAMES` | 8 / 15 | When a lost gate counts as "driving through it", and for how long to go straight. |

## Troubleshooting

- **`Camera frontend has timed out`**: the Pi sees the sensor but gets no
  frames. Reseat the ribbon cable at both ends (contacts facing the right
  way) and check the power supply. `rpicam-hello --timeout 5000` tests the
  camera on its own.
- **`Camera is already in use`**: another process holds the camera; stop it
  and rerun.
- **macOS: `Cannot open the camera`**: allow camera access for your terminal
  in System Settings → Privacy & Security → Camera, then restart the terminal.
