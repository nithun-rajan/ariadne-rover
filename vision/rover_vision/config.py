"""Tuning constants shared by the whole vision pipeline.

Everything that is a "knob" lives here so the detector, tracker and steering
code contain logic only.
"""

# ===== CAMERA (Raspberry Pi, OV5647) =====
IMG_WIDTH = 1280
IMG_HEIGHT = 720
FRAMERATE = 25
# libcamera's naming is counter-intuitive: "RGB888" yields numpy arrays in
# OpenCV's BGR channel order, so frames can go straight into cv2.
CAMERA_FORMAT = "RGB888"
CAMERA_RAW_WIDTH = 1296            # 2x2-binned full-FOV sensor mode
CAMERA_RAW_HEIGHT = 972
CAMERA_BUFFER_COUNT = 4
CAMERA_STARTUP_RETRIES = 3
CAMERA_METADATA_LOG_INTERVAL = 50  # frames between exposure/gain log lines

# ===== WEB STREAM =====
STREAM_PORT = 8080
STREAM_JPEG_QUALITY = 85

# ===== SQUARE CANDIDATE DETECTION =====
BLUR_KERNEL_SIZE = 5
ADAPTIVE_BLOCK_SIZE = 11           # odd, in pixels
ADAPTIVE_C = 2
MIN_MARKER_AREA = 1000             # px^2
MAX_MARKER_AREA = 50000            # px^2
MIN_MARKER_SIDE = 20               # px
POLY_APPROX_EPSILON = 0.04         # fraction of perimeter
MAX_ASPECT_RATIO = 1.5             # min-area-rect long/short side
MAX_SIDE_RATIO = 1.6               # longest/shortest polygon side

# ===== MARKER DECODING =====
# Each marker is a black square border (20% of the side on each edge) around
# a 4x4 grid of black/white cells. 1 = black, 0 = white. Grids are matched
# in all four rotations, so card orientation on the gate post does not matter.
MARKER_PATCH_SIZE = 80             # px, side of the rectified patch
MARKER_BORDER_FRACTION = 0.2

PATTERNS_PI = {
    'left': [[0, 1, 0, 1],
             [0, 0, 0, 0],
             [0, 1, 1, 1],
             [0, 0, 0, 0]],

    'right': [[1, 0, 1, 0],
              [1, 1, 0, 0],
              [1, 1, 0, 1],
              [0, 0, 1, 1]],
}

# Patterns captured with calibrate_patterns.py on a laptop webcam are saved to
# this file (next to the scripts) and preferred by run_webcam.py.
WEBCAM_PATTERNS_FILE = 'webcam_patterns.json'

# A few flipped cells are tolerated so blur and glare do not reject a marker;
# the two patterns differ in far more cells than this in every rotation.
MAX_HAMMING_DISTANCE = 2
# Two detections whose centres are closer than this fraction of the marker
# size are the same physical marker (outer and inner contour of one border).
DUPLICATE_CENTER_FRACTION = 0.35

# ===== GATE PAIRING =====
AREA_MATCH_THRESHOLD = 0.35        # max relative size difference of a pair
ANGLE_MAX_DEGREES = 75             # max tilt of the left-right line
GATE_MEMORY_FRAMES = 5             # hold the last gate through short dropouts
GATE_SMOOTHING_ALPHA = 0.35        # EMA weight: lower = steadier, higher = snappier

# ===== STEERING =====
LETTER_NUM_ZONES = 26              # A..Z across the frame width
STEER_ZONE_LEFT = IMG_WIDTH / 3    # LED indicator zone boundaries
STEER_ZONE_RIGHT = 2 * IMG_WIDTH / 3

# ===== GATE CROSSING STATE MACHINE =====
GATE_PRESENT_THRESHOLD = 3         # frames before a gate counts as locked on
GATE_ABSENT_THRESHOLD = 8          # frames of absence that mean "driving through"
COOLDOWN_FRAMES = 15               # frames driven straight while clearing a gate
NO_GATE_CHAR = '?'
STRAIGHT_CHAR = 'M'

# ===== RASPBERRY PI I/O =====
LED_PINS = {                       # BCM numbering
    'stop': 17,
    'strong_left': 27,
    'light_left': 22,
    'go': 23,
    'light_right': 24,
    'strong_right': 6,
}
SERIAL_TX_PIN = 14                 # GPIO14 (TXD) -> Pico GP17 (UART0 RX)
SERIAL_PORT = '/dev/ttyAMA0'
SERIAL_BAUD_RATE = 9600
SERIAL_RATE_HZ = 25                # matches the Pico control loop
