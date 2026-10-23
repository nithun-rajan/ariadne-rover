#include "rover_move.hpp"

int main() {
    MachineContext ctx;
    DriveState     state = DriveState::BOOT;

    while (true) {
        sleep_ms(CONTROL_PERIOD_MS);

        bool got_letter = false;
        if (state != DriveState::BOOT) {
            got_letter = updateContextFromSerial(ctx);
        }

        switch (state) {
            case DriveState::BOOT:
                initHardware(ctx);
                state = DriveState::WAIT_LINK;
                break;

            case DriveState::WAIT_LINK:
                if (got_letter) state = DriveState::ACTIVE_DRIVE;
                break;

            case DriveState::ACTIVE_DRIVE:
                driveFromLetter(ctx, ctx.last_letter);
                // The Pi sends every frame, so silence means it has crashed
                // or the wire is loose: stop immediately, no slew.
                if (isLinkTimedOut(ctx)) {
                    stopMotors(ctx);
                    state = DriveState::FAILSAFE_STOP;
                }
                break;

            case DriveState::FAILSAFE_STOP:
                if (got_letter) state = DriveState::ACTIVE_DRIVE;
                break;
        }
    }
}
