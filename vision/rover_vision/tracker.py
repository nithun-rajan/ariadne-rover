"""Stage 4: temporal smoothing of the chosen gate."""

from . import config


def _lerp(a, b, alpha):
    return (1.0 - alpha) * float(a) + alpha * float(b)


class GateTracker:
    """Exponential moving average over the gate centre and width.

    Smoothing stops single-frame corner jitter from twitching the steering,
    and the last gate is held for a few frames so a brief miss (motion blur,
    a marker clipping the frame edge) does not drop the lock.
    """

    def __init__(self, memory_frames=config.GATE_MEMORY_FRAMES,
                 alpha=config.GATE_SMOOTHING_ALPHA):
        self.memory_frames = memory_frames
        self.alpha = alpha
        self.reset()

    def reset(self):
        self.last_gate = None
        self.missed_frames = 0

    def update(self, gate):
        """Feed this frame's gate (or None); returns the tracked gate or None.

        A held gate is returned with 'stale' = True.
        """
        if gate is not None:
            self.missed_frames = 0
            smoothed = dict(gate, stale=False)
            if self.last_gate is not None:
                old = self.last_gate
                smoothed['center'] = [_lerp(old['center'][0], gate['center'][0], self.alpha),
                                      _lerp(old['center'][1], gate['center'][1], self.alpha)]
                smoothed['width'] = _lerp(old['width'], gate['width'], self.alpha)
            self.last_gate = smoothed
            return smoothed

        if self.last_gate is None:
            return None

        self.missed_frames += 1
        if self.missed_frames > self.memory_frames:
            self.reset()
            return None
        return dict(self.last_gate, stale=True, missed_frames=self.missed_frames)
