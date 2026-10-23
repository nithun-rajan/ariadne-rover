"""Stage 5: turn the gate's horizontal position into a steering command."""

from . import config


def x_to_letter(x, uppercase=True, img_width=config.IMG_WIDTH,
                num_zones=config.LETTER_NUM_ZONES):
    """Map a pixel x coordinate to one of 26 steering letters.

    The frame is split into 26 equal vertical zones: 'A' is the far left,
    'M'/'N' straddle the centre and 'Z' is the far right. The Pico firmware
    converts the letter into differential wheel speeds.
    """
    x = max(0.0, min(float(x), float(img_width)))
    zone = min(int(x / (img_width / num_zones)), num_zones - 1)
    return chr((ord('A') if uppercase else ord('a')) + zone)


def x_to_command(x, img_width=config.IMG_WIDTH):
    """Coarse five-way command, used for the indicator LEDs and the overlay."""
    left = config.STEER_ZONE_LEFT * img_width / config.IMG_WIDTH
    right = config.STEER_ZONE_RIGHT * img_width / config.IMG_WIDTH
    if x < left / 2:
        return 'strong_left'
    if x < left:
        return 'light_left'
    if x <= right:
        return 'go'
    if x <= right + (img_width - right) / 2:
        return 'light_right'
    return 'strong_right'


def gate_to_command(gate, img_width=config.IMG_WIDTH):
    """Command for a gate dict, or 'stop' when there is no gate."""
    if gate is None:
        return 'stop'
    return x_to_command(gate['center'][0], img_width)
