"""Stage 3: pair left/right markers into gates and pick the one to drive at."""

from . import config
from .geometry import angle_from_horizontal, distance, midpoint


def gate_score(area_diff, angle, width,
               area_threshold=config.AREA_MATCH_THRESHOLD,
               angle_max=config.ANGLE_MAX_DEGREES):
    """Rank candidate gates.

    Width dominates (a wider gate is closer, so it is the next one to pass);
    well-matched marker sizes and a level left-right line add confidence.
    """
    area_quality = max(0.0, 1.0 - area_diff / area_threshold)
    angle_quality = max(0.0, 1.0 - angle / angle_max)
    return width * (0.55 + 0.30 * area_quality + 0.15 * angle_quality)


def find_gates(markers,
               area_threshold=config.AREA_MATCH_THRESHOLD,
               angle_max=config.ANGLE_MAX_DEGREES):
    """Return every plausible (left, right) marker pairing as a gate dict.

    Two markers on the same gate are at a similar distance from the camera,
    so their apparent areas must match and the line between them must be
    close to horizontal.
    """
    lefts = [m for m in markers if m['type'] == 'left']
    rights = [m for m in markers if m['type'] == 'right']

    gates = []
    for left in lefts:
        for right in rights:
            larger = max(left['area'], right['area'])
            smaller = min(left['area'], right['area'])
            area_diff = (larger - smaller) / larger if larger > 0 else 1.0
            angle = angle_from_horizontal(left['center'], right['center'])
            if area_diff > area_threshold or angle > angle_max:
                continue

            width = distance(left['center'], right['center'])
            gates.append({
                'left': left,
                'right': right,
                'center': midpoint(left['center'], right['center']),
                'width': width,
                'area_diff': area_diff,
                'angle': angle,
                'score': gate_score(area_diff, angle, width, area_threshold, angle_max),
                'stale': False,
            })
    return gates


def best_gate(gates):
    """The highest-scoring gate, or None."""
    return max(gates, key=lambda g: g['score']) if gates else None
