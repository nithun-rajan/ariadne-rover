import pytest

from rover_vision import config
from rover_vision.navigator import CLEARING, DROPOUT, SEARCHING, TRACKING, GateNavigator
from rover_vision.pipeline import GatePipeline
from rover_vision.steering import gate_to_command, x_to_letter
from tests.synthetic import scene

W = config.IMG_WIDTH


@pytest.mark.parametrize('x,letter', [(0, 'A'), (W / 2, 'N'), (W / 2 - 1, 'M'),
                                      (W - 1, 'Z'), (W, 'Z'), (-50, 'A'), (W + 50, 'Z')])
def test_x_to_letter(x, letter):
    assert x_to_letter(x) == letter
    assert x_to_letter(x, uppercase=False) == letter.lower()


def test_coarse_commands():
    assert gate_to_command(None) == 'stop'
    assert gate_to_command({'center': [W / 2, 0]}) == 'go'
    assert gate_to_command({'center': [10, 0]}) == 'strong_left'
    assert gate_to_command({'center': [W - 10, 0]}) == 'strong_right'


def drive(nav, frames):
    return [nav.update(g) for g in frames]


def test_searching_sends_stop():
    nav = GateNavigator()
    assert drive(nav, [None] * 3) == [('?', False)] * 3
    assert nav.state == SEARCHING


def test_full_gate_crossing_cycle():
    nav = GateNavigator(present_threshold=3, absent_threshold=4, cooldown_frames=2)
    centre = {'center': [W / 2, 360]}

    for _ in range(3):
        letter, _ = nav.update(centre)
    assert (letter, nav.state) == ('N', TRACKING)

    # Markers leave the frame as the rover reaches the gate: keep steering.
    for _ in range(3):
        assert nav.update(None) == ('N', False)
        assert nav.state == DROPOUT

    # Gone long enough -> drive straight through.
    assert nav.update(None) == ('M', False)
    assert nav.state == CLEARING
    assert nav.update(centre) == ('M', False)    # gates ignored while clearing
    assert nav.update(None) == ('M', True)       # cooldown done: gate passed

    assert nav.gates_passed == 1
    assert nav.update({'center': [0, 360]}) == ('a', False)   # next gate: lower case


def test_a_glimpse_is_not_a_lock():
    nav = GateNavigator(present_threshold=3, absent_threshold=2)
    nav.update({'center': [W / 2, 360]})
    assert drive(nav, [None] * 5)[-1] == ('?', False)
    assert nav.gates_passed == 0


def test_end_to_end_on_a_synthetic_frame():
    frame = scene([
        {'pattern': config.PATTERNS_PI['left'], 'centre': (200, 380), 'side': 110},
        {'pattern': config.PATTERNS_PI['right'], 'centre': (560, 360), 'side': 110},
    ])
    result = GatePipeline().process(frame)
    assert result.gate is not None
    assert result.gate['center'][0] == pytest.approx(380, abs=3)
    assert result.command == 'light_left'
    assert x_to_letter(result.gate['center'][0]) == 'H'
