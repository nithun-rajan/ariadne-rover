import pytest

from rover_vision.gates import best_gate, find_gates
from rover_vision.tracker import GateTracker


def marker(kind, x, y=360, area=10000):
    return {'type': kind, 'center': (x, y), 'area': area}


def test_pairs_matching_left_and_right():
    gates = find_gates([marker('left', 400), marker('right', 800)])
    assert len(gates) == 1
    assert gates[0]['center'] == [600, 360]
    assert gates[0]['width'] == pytest.approx(400)


def test_rejects_mismatched_sizes_and_steep_pairs():
    assert find_gates([marker('left', 400, area=10000), marker('right', 800, area=4000)]) == []
    assert find_gates([marker('left', 400, y=0), marker('right', 450, y=700)]) == []


def test_unknown_markers_never_form_gates():
    assert find_gates([marker('unknown', 400), marker('right', 800)]) == []


def test_best_gate_prefers_the_nearer_wider_gate():
    far = [marker('left', 550, area=2500), marker('right', 700, area=2500)]
    near = [marker('left', 200, area=12000), marker('right', 1000, area=12000)]
    gate = best_gate(find_gates(far + near))
    assert gate['width'] == pytest.approx(800)
    assert best_gate([]) is None


def gate_at(x, width=400.0):
    return {'center': [x, 360.0], 'width': width}


def test_tracker_smooths_jumps():
    tracker = GateTracker(alpha=0.5)
    tracker.update(gate_at(600))
    assert tracker.update(gate_at(700))['center'][0] == pytest.approx(650)


def test_tracker_holds_then_drops():
    tracker = GateTracker(memory_frames=2)
    tracker.update(gate_at(600))
    held = [tracker.update(None) for _ in range(3)]
    assert [g is not None and g['stale'] for g in held[:2]] == [True, True]
    assert held[2] is None
    assert tracker.update(gate_at(100))['center'][0] == 100    # fresh start, no blend
