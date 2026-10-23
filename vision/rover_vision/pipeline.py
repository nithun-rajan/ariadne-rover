"""One frame through detection, pairing and tracking."""

from dataclasses import dataclass, field

import cv2

from .gates import best_gate, find_gates
from .markers import MarkerDetector
from .steering import gate_to_command
from .tracker import GateTracker


@dataclass
class FrameResult:
    markers: list
    raw_gate: dict = None     # best gate seen in this frame
    gate: dict = None         # tracked (smoothed / held) gate
    command: str = 'stop'

    @property
    def gate_status(self):
        if self.gate is None:
            return 'no'
        return 'hold' if self.gate.get('stale') else 'yes'


@dataclass
class GatePipeline:
    detector: MarkerDetector = field(default_factory=MarkerDetector)
    tracker: GateTracker = field(default_factory=GateTracker)

    def process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        markers = self.detector.detect(frame, gray=gray)
        raw_gate = best_gate(find_gates(markers))
        gate = self.tracker.update(raw_gate)
        return FrameResult(markers, raw_gate, gate,
                           gate_to_command(gate, img_width=frame.shape[1]))
