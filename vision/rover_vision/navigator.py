"""Stage 6: the gate-crossing state machine.

Close to a gate the markers slide out of the field of view, so "no gate
visible" is ambiguous: either nothing has been found yet, or the rover is
in the middle of driving through one. The navigator tells these apart:

    SEARCHING --gate seen--> TRACKING --gate lost briefly--> DROPOUT
        ^                       |   ^__________________________|
        |                       | gate lost for GATE_ABSENT_THRESHOLD frames
        |                       v   (after a solid lock)
        +---- gate passed --- CLEARING (drive straight for COOLDOWN_FRAMES)

Letter case alternates per gate (upper for gates 1, 3, ...; lower for 2,
4, ...) so the gate count is visible in the serial stream.
"""

from . import config
from .steering import x_to_letter

SEARCHING = 'SEARCHING'
TRACKING = 'TRACKING'
DROPOUT = 'DROPOUT'
CLEARING = 'CLEARING'


class GateNavigator:
    def __init__(self, img_width=config.IMG_WIDTH,
                 present_threshold=config.GATE_PRESENT_THRESHOLD,
                 absent_threshold=config.GATE_ABSENT_THRESHOLD,
                 cooldown_frames=config.COOLDOWN_FRAMES,
                 no_gate_char=config.NO_GATE_CHAR,
                 straight_char=config.STRAIGHT_CHAR):
        self.img_width = img_width
        self.present_threshold = present_threshold
        self.absent_threshold = absent_threshold
        self.cooldown_frames = cooldown_frames
        self.no_gate_char = no_gate_char
        self.straight_char = straight_char

        self.gates_passed = 0
        self.state = SEARCHING
        self._reset_lock()
        self.clearing_frames_left = 0

    def _reset_lock(self):
        self.frames_present = 0
        self.frames_absent = 0
        self.locked = False
        self.last_letter = self.no_gate_char

    @property
    def uppercase(self):
        return self.gates_passed % 2 == 0

    def _straight(self):
        return self.straight_char if self.uppercase else self.straight_char.lower()

    def update(self, gate):
        """Advance one frame. Returns (letter, gate_passed_this_frame)."""
        passed = False

        if self.clearing_frames_left > 0:
            self.state = CLEARING
            letter = self._straight()
            self.clearing_frames_left -= 1
            if self.clearing_frames_left == 0:
                self.gates_passed += 1
                self._reset_lock()
                self.state = SEARCHING
                passed = True

        elif gate is not None:
            self.frames_present += 1
            self.frames_absent = 0
            if self.frames_present >= self.present_threshold:
                self.locked = True
            letter = x_to_letter(gate['center'][0], self.uppercase, self.img_width)
            self.last_letter = letter
            self.state = TRACKING

        else:
            self.frames_present = 0
            self.frames_absent += 1
            if self.locked and self.frames_absent >= self.absent_threshold:
                self.clearing_frames_left = self.cooldown_frames
                letter = self._straight()
                self.state = CLEARING
            elif self.locked:
                letter = self.last_letter
                self.state = DROPOUT
            else:
                letter = self.no_gate_char
                self.state = SEARCHING

        return letter, passed
