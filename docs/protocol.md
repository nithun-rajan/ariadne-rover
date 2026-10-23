# Pi → Pico serial protocol

| | |
|---|---|
| Link | Pi GPIO14 (TXD, `/dev/ttyAMA0`) → Pico GP17 (UART0 RX), common ground |
| Format | 9600 baud, 8N1, ASCII |
| Rate | one message per vision frame, capped at 25 Hz |
| Message | one character followed by `\n` |

## Characters

| Character | Meaning |
|---|---|
| `A`–`Z` | Gate centre is in zone 0–25 of the frame (left → right). |
| `a`–`z` | Same zones; lower case is used on even-numbered gates. |
| `M` / `m` | Also sent while driving straight through a gate (`CLEARING`). |
| `?` | No gate: soft stop (wheels slew down to zero over about 0.6 s). |

Letter case lets anyone watching the serial line see which gate the rover
is on. The Pico treats both cases identically.

The Pico ignores newlines and any other byte; each control cycle it acts
on the **most recent** valid character, so the newline is only there for
humans reading the stream.

## Liveness

The stream is a dead man's switch. The Pi must keep sending, even when
the letter does not change. If the Pico receives no valid character for
**300 ms**, it stops both motors at once (no slew) and waits for the
stream to resume.

| Pi behaviour | Rover behaviour |
|---|---|
| keeps sending `M` | drives straight at cruise speed |
| sends `G`, `H`, … `M` as the gate centres | smooth curve onto the gate |
| sends `?` | gentle stop |
| goes silent (crash, cable) | immediate stop after 300 ms |
