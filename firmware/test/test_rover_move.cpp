// Host-side tests for the motor controller logic, built against the stub
// SDK headers in test/stubs. Run with:  make -C firmware/test

#include <cstdio>
#include <cstdlib>
#include <string>

#include "../src/rover_move.hpp"

static int failures = 0;

#define CHECK(cond)                                                       \
    do {                                                                  \
        if (!(cond)) {                                                    \
            std::printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond);   \
            ++failures;                                                   \
        }                                                                 \
    } while (0)

static void expectTargets(char c, int l, int r) {
    int tl, tr;
    targetsForLetter(c, tl, tr);
    if (tl != l || tr != r) {
        std::printf("FAIL '%c': got (%d, %d), want (%d, %d)\n", c, tl, tr, l, r);
        ++failures;
    }
}

static void testSteeringTable() {
    expectTargets('A', 120, -120);
    expectTargets('B', 120, 24);
    expectTargets('H', 120, 24);
    expectTargets('I', 120, 33);
    expectTargets('J', 120, 52);
    for (char c = 'K'; c <= 'P'; ++c) expectTargets(c, 120, 120);   // deadband
    expectTargets('Q', 52, 120);
    expectTargets('R', 33, 120);
    expectTargets('S', 24, 120);
    expectTargets('Y', 24, 120);
    expectTargets('Z', -120, 120);
    expectTargets('?', 0, 0);
    expectTargets('#', 0, 0);
    expectTargets('m', 120, 120);                                   // lower case = same zones
}

static void testSteeringIsSymmetric() {
    for (int z = 0; z < 26; ++z) {
        int l1, r1, l2, r2;
        targetsForLetter('A' + z, l1, r1);
        targetsForLetter('Z' - z, l2, r2);
        CHECK(l1 == r2 && r1 == l2);
    }
}

static void testSlewLimitsAcceleration() {
    MachineContext ctx;
    driveFromLetter(ctx, 'M');
    CHECK(ctx.curr_l == SLEW && ctx.curr_r == SLEW);
    for (int i = 0; i < 100; ++i) driveFromLetter(ctx, 'M');
    CHECK(ctx.curr_l == 120 && ctx.curr_r == 120);
    driveFromLetter(ctx, '?');
    CHECK(ctx.curr_l == 120 - SLEW);
}

static void testReceiverKeepsNewestLetter() {
    MachineContext ctx;
    host::now_ms = 1000;
    for (char c : std::string("A\nB\nxx\n7\nC\n")) host::uart_rx.push_back(c);
    CHECK(updateContextFromSerial(ctx));
    CHECK(ctx.last_letter == 'C');
    CHECK(host::uart_rx.empty());
    CHECK(!updateContextFromSerial(ctx));   // nothing new
    for (char c : std::string("\n\r 1")) host::uart_rx.push_back(c);
    CHECK(!updateContextFromSerial(ctx));   // only junk
    CHECK(ctx.last_letter == 'C');
}

static void testFailsafeTimeout() {
    MachineContext ctx;
    CHECK(!isLinkTimedOut(ctx));            // never received: not a timeout
    host::now_ms = 5000;
    host::uart_rx.push_back('M');
    updateContextFromSerial(ctx);
    host::now_ms += RX_TIMEOUT_MS;
    CHECK(!isLinkTimedOut(ctx));
    host::now_ms += 1;
    CHECK(isLinkTimedOut(ctx));
}

static void testPwmScaling() {
    MachineContext ctx;
    initHardware(ctx);
    CHECK(ctx.pwm_wrap == 6250);            // 125 MHz / 20 kHz
    setMotorSpeeds(ctx, MAX_PWM, -MAX_PWM);
    CHECK(host::pwm_level[M1_PWM_PIN] == 6250 && host::dir[M1_DIR_PIN] == 1);
    CHECK(host::pwm_level[M2_PWM_PIN] == 6250 && host::dir[M2_DIR_PIN] == 0);
    setMotorSpeeds(ctx, 1000, 0);           // clamped
    CHECK(host::pwm_level[M1_PWM_PIN] == 6250);
}

int main() {
    testSteeringTable();
    testSteeringIsSymmetric();
    testSlewLimitsAcceleration();
    testReceiverKeepsNewestLetter();
    testFailsafeTimeout();
    testPwmScaling();

    if (failures) {
        std::printf("%d check(s) failed\n", failures);
        return EXIT_FAILURE;
    }
    std::printf("all firmware tests passed\n");
    return EXIT_SUCCESS;
}
