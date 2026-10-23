"""Outputs from the Pi: the UART link to the Pico and the indicator LEDs.

Each output has a no-op twin so the full pipeline can run on a bench with no
rover attached (``run_rover.py --no-rover``).
"""

import time

from . import config


class SerialLink:
    """Sends one steering letter + newline to the Pico at a fixed rate.

    The Pico treats the stream as a dead man's switch: if no valid letter
    arrives for 300 ms it cuts the motors. So a letter must be sent every
    cycle, including repeats of the same letter.
    """

    def __init__(self, port=config.SERIAL_PORT, baud=config.SERIAL_BAUD_RATE,
                 rate_hz=config.SERIAL_RATE_HZ):
        import serial   # pyserial; only needed on the rover

        self._serial = serial.Serial(port, baud, timeout=1)
        self._interval = 1.0 / rate_hz
        self._last_tx = 0.0
        print(f'[uart] {port} @ {baud} baud, {rate_hz} Hz')

    def send(self, letter):
        now = time.monotonic()
        if now - self._last_tx < self._interval:
            return False
        self._serial.write(f'{letter}\n'.encode('ascii'))
        self._last_tx = now
        return True

    def close(self):
        self._serial.close()


class NullLink:
    def send(self, letter):
        return False

    def close(self):
        pass


class LedPanel:
    """One indicator LED per coarse steering command."""

    def __init__(self, pins=config.LED_PINS):
        import RPi.GPIO as GPIO   # only available on the Pi

        self._gpio = GPIO
        self._pins = pins
        GPIO.setmode(GPIO.BCM)
        for pin in pins.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self._active = None

    def show(self, command):
        if command == self._active:
            return
        for name, pin in self._pins.items():
            self._gpio.output(pin, self._gpio.HIGH if name == command else self._gpio.LOW)
        self._active = command

    def close(self):
        self._gpio.cleanup(list(self._pins.values()))


class NullLeds:
    def show(self, command):
        pass

    def close(self):
        pass
