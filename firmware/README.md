# Firmware

C++ motor controller for the Raspberry Pi Pico. It reads steering letters
from the Pi over UART and drives two DC motors with slew-limited
differential PWM. See [`docs/protocol.md`](../docs/protocol.md) for the
message format.

## State machine

```
BOOT ──► WAIT_LINK ──first letter──► ACTIVE_DRIVE ◄──letter── FAILSAFE_STOP
                                          │                        ▲
                                          └── 300 ms silence ──────┘
```

## Wiring

| Pico | Connects to |
|---|---|
| GP0 / GP1 | Motor 1 PWM / DIR |
| GP11 / GP10 | Motor 2 PWM / DIR |
| GP17 (UART0 RX) | Pi GPIO14 (TXD) |
| GND | Pi GND |

PWM runs at about 20 kHz (above hearing, so the motors don't whine).

## Build and flash

Requires the [Pico SDK](https://github.com/raspberrypi/pico-sdk) (2.x) and
`arm-none-eabi-gcc`.

```bash
cd firmware
mkdir -p build && cd build
cmake -DPICO_SDK_PATH=/path/to/pico-sdk ..
make -j rover_move
```

Hold BOOTSEL while plugging in the Pico, then copy `build/rover_move.uf2`
to the `RPI-RP2` drive that appears.

## Tests

The control logic (steering table, deadband, slew limiting, serial parsing,
failsafe timing, PWM scaling) is compiled for the host against minimal SDK
stubs in `test/stubs/`:

```bash
make -C test
```

## Tuning

Constants are at the top of [`src/rover_move.hpp`](src/rover_move.hpp):
`BASE_PWM` (cruise speed), `SLEW` (smoothness), `STRAIGHT_FIRST`/`STRAIGHT_LAST`
(deadband width), `MIN_INNER_PWM` (how hard a turn can get before the edge
zones), and `RX_TIMEOUT_MS` (failsafe).
