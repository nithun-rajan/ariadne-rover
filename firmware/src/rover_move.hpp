#ifndef ROVER_MOVE_HPP
#define ROVER_MOVE_HPP

// Ariadne motor controller (Raspberry Pi Pico, RP2040)
//
// Receives one steering letter per control cycle from the Raspberry Pi over
// UART0 and turns it into slew-limited differential PWM for two DC motors.

#include <cstdlib>
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "hardware/uart.h"

// ============================================================
//  Drive FSM states
//   BOOT          - one-shot hardware init
//   WAIT_LINK     - motors off until the first valid letter arrives
//   ACTIVE_DRIVE  - letter -> motor speeds every cycle
//   FAILSAFE_STOP - no valid letter for RX_TIMEOUT_MS: motors off until
//                   the Pi starts sending again
// ============================================================
enum class DriveState {
    BOOT,
    WAIT_LINK,
    ACTIVE_DRIVE,
    FAILSAFE_STOP
};

// ============================================================
//  Tuning
// ============================================================
constexpr uint     CONTROL_PERIOD_MS = 40;    // 25 Hz, matches the Pi TX rate
constexpr uint32_t RX_TIMEOUT_MS     = 300;   // dead man's switch
constexpr int      MAX_PWM           = 255;
constexpr float    BASE_PWM          = 120.0f; // cruising speed, both wheels
constexpr int      MIN_INNER_PWM     = 24;    // inner wheel floor (non-edge zones)
constexpr int      SLEW              = 8;     // max PWM change per cycle
constexpr int      STRAIGHT_FIRST    = 10;    // zones K..P drive straight
constexpr int      STRAIGHT_LAST     = 15;
constexpr uint32_t PWM_FREQ_HZ       = 20000;
constexpr uint     UART_BAUD         = 9600;

// ============================================================
//  Pins
//   M1: DIR = GP1,  PWM = GP0
//   M2: DIR = GP10, PWM = GP11
//   UART0: TX = GP16, RX = GP17 (wired to Pi GPIO14 / TXD)
// ============================================================
constexpr uint M1_DIR_PIN  = 1;
constexpr uint M1_PWM_PIN  = 0;
constexpr uint M2_DIR_PIN  = 10;
constexpr uint M2_PWM_PIN  = 11;
constexpr uint UART_TX_PIN = 16;
constexpr uint UART_RX_PIN = 17;

// All mutable runtime state in one place.
struct MachineContext {
    uint16_t pwm_wrap    = 0;
    uint32_t last_rx_ms  = 0;     // time of the last valid letter
    char     last_letter = '?';
    int      curr_l      = 0;     // slew-limited outputs actually applied
    int      curr_r      = 0;
};

// ============================================================
//  Motor primitives
// ============================================================
inline void setMotor(uint dir_pin, uint pwm_pin, uint16_t wrap, int pwm) {
    gpio_put(dir_pin, pwm >= 0 ? 1 : 0);
    int speed = std::abs(pwm);
    if (speed > MAX_PWM) speed = MAX_PWM;
    pwm_set_gpio_level(pwm_pin, (uint16_t)((speed * wrap) / MAX_PWM));
}

inline void setMotorSpeeds(const MachineContext& ctx, int pwm1, int pwm2) {
    setMotor(M1_DIR_PIN, M1_PWM_PIN, ctx.pwm_wrap, pwm1);
    setMotor(M2_DIR_PIN, M2_PWM_PIN, ctx.pwm_wrap, pwm2);
}

inline void stopMotors(MachineContext& ctx) {
    setMotorSpeeds(ctx, 0, 0);
    ctx.curr_l = 0;
    ctx.curr_r = 0;
}

inline void initMotorPins(uint dir_pin, uint pwm_pin, uint16_t wrap) {
    gpio_init(dir_pin);
    gpio_set_dir(dir_pin, GPIO_OUT);
    gpio_set_function(pwm_pin, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(pwm_pin);
    pwm_set_wrap(slice, wrap);
    pwm_set_enabled(slice, true);
}

inline void initHardware(MachineContext& ctx) {
    // ~20 kHz PWM: above hearing range, so the motors do not whine.
    ctx.pwm_wrap = (uint16_t)(clock_get_hz(clk_sys) / PWM_FREQ_HZ);
    initMotorPins(M1_DIR_PIN, M1_PWM_PIN, ctx.pwm_wrap);
    initMotorPins(M2_DIR_PIN, M2_PWM_PIN, ctx.pwm_wrap);
    stopMotors(ctx);

    uart_init(uart0, UART_BAUD);
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);
}

// ============================================================
//  Letter -> motor speed mapping
//
//  The Pi splits the camera frame into 26 zones and sends the zone of the
//  gate centre as a letter (A..Z, or a..z on alternate gates). The zone is
//  mapped to t in [-1, +1]; one wheel stays at BASE and the other slows:
//
//    left  = BASE - clamp(t, 0, 1) * 2 * BASE
//    right = BASE + clamp(t, -1, 0) * 2 * BASE
//
//  Resulting targets (left, right) at BASE = 120:
//    A          zone 0       spin in place     ( 120, -120)
//    B..H       zones 1-7    hard turn         ( 120,   24)  inner floor
//    I..J       zones 8-9    gentle turn       ( 120, 33..52)
//    K..P       zones 10-15  straight          ( 120,  120)  deadband
//    Q..R       zones 16-17  gentle turn       (52..33, 120)
//    S..Y       zones 18-24  hard turn         (  24,  120)
//    Z          zone 25      spin in place     (-120,  120)
//    ? / other               stop              (   0,    0)
//
//  The wide deadband stops small CV jitter from nudging the rover side to
//  side while it crosses a gate. Outputs then move towards the target by
//  at most SLEW per cycle, so a letter change becomes a smooth curve
//  instead of a jerk (0 -> BASE takes ~0.6 s).
// ============================================================
inline void targetsForLetter(char c, int& target_l, int& target_r) {
    int zone = -1;
    if      (c >= 'A' && c <= 'Z') zone = c - 'A';
    else if (c >= 'a' && c <= 'z') zone = c - 'a';

    if (zone < 0) {
        target_l = 0;
        target_r = 0;
        return;
    }

    float t = 0.0f;
    if (zone < STRAIGHT_FIRST || zone > STRAIGHT_LAST) {
        t = (zone - 12.5f) / 12.5f;
        if (t < -1.0f) t = -1.0f;
        if (t >  1.0f) t =  1.0f;
    }
    float t_pos = (t > 0.0f) ? t : 0.0f;
    float t_neg = (t < 0.0f) ? t : 0.0f;

    target_l = (int)(BASE_PWM - t_pos * 2.0f * BASE_PWM);
    target_r = (int)(BASE_PWM + t_neg * 2.0f * BASE_PWM);

    // Only the extreme edge zones may reverse a wheel; everything else keeps
    // both wheels moving forward so turns stay smooth.
    if (zone > 0 && zone < 25) {
        if (target_l < MIN_INNER_PWM) target_l = MIN_INNER_PWM;
        if (target_r < MIN_INNER_PWM) target_r = MIN_INNER_PWM;
    }
}

inline int slewTowards(int current, int target) {
    int delta = target - current;
    if (delta >  SLEW) delta =  SLEW;
    if (delta < -SLEW) delta = -SLEW;
    return current + delta;
}

inline void driveFromLetter(MachineContext& ctx, char c) {
    int target_l, target_r;
    targetsForLetter(c, target_l, target_r);
    ctx.curr_l = slewTowards(ctx.curr_l, target_l);
    ctx.curr_r = slewTowards(ctx.curr_r, target_r);
    setMotorSpeeds(ctx, ctx.curr_l, ctx.curr_r);
}

// ============================================================
//  Serial receiver
//
//  Drains everything waiting in the UART FIFO and keeps only the newest
//  valid letter, so the rover always acts on the freshest frame and a
//  backlog can never build up. Newlines and any other bytes are ignored.
//  Returns true if a valid letter arrived this cycle.
// ============================================================
inline bool isValidLetter(char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '?';
}

inline bool updateContextFromSerial(MachineContext& ctx) {
    char latest = '\0';
    while (uart_is_readable(uart0)) {
        char c = uart_getc(uart0);
        if (isValidLetter(c)) latest = c;
    }
    if (latest == '\0') return false;

    ctx.last_letter = latest;
    ctx.last_rx_ms  = to_ms_since_boot(get_absolute_time());
    return true;
}

// False until the first letter has been received.
inline bool isLinkTimedOut(const MachineContext& ctx) {
    if (ctx.last_rx_ms == 0) return false;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    return (now - ctx.last_rx_ms) > RX_TIMEOUT_MS;
}

#endif // ROVER_MOVE_HPP
