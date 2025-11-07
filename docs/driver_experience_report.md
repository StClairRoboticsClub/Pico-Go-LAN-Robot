# Driver Experience Report – Pico-Go LAN Robot

## Control Pipeline Overview
- Xbox inputs flow through `controller/controller_xbox.py:545-790`, get serialized as UDP packets (`controller/controller_xbox.py:682-715`), and are consumed by the Pico W UDP server (`firmware/ws_server.py:283-360`).
- Drive commands are mixed into wheel PWM inside `firmware/motor.py:81-95`, respecting `MAX_SPEED`/`TURN_RATE` from `firmware/config.py:124-130`.
- Safety is enforced by the watchdog (`firmware/watchdog.py:24-86`, timeout 200 ms per `firmware/config.py:35`).

## Current UX Gains
- Right trigger now commands forward motion and left trigger handles reverse, eliminating the LB toggle and matching gamer muscle memory (`controller/controller_xbox.py:595-606`).
- Steering right now yields a clockwise yaw (`controller/controller_xbox.py:608-610`), aligning stick direction with chassis rotation.

## Remaining Gaps & Targets
1. **Input Shaping**
   - Problem: Deadbanded triggers remap straight to ±1, making small motions produce ~70 % PWM steps.
   - Target: Add configurable expo (square/cubic or piecewise) so low-stick motion limits PWM to ≤30 % while keeping full output at extremes. Expose constants in controller config.

2. **Wheel Mixing & Calibration**
   - Problem: Sum-and-clamp logic clips whichever wheel exceeds ±1, altering curvature mid-turn; no compensation for left/right PWM mismatch or battery sag.
   - Target: Normalize wheel commands to preserve curvature, then multiply by per-wheel calibration gains stored in firmware config. Add a calibration script that logs actual wheel speed vs. PWM so the TB6612FNG channels can be balanced to within 5 %.

3. **Smoothing vs. Watchdog**
   - Problem: Raw joystick steps become immediate PWM jumps, yet any filtering risks tripping the 200 ms watchdog.
   - Target: Introduce slew-rate limiters (controller + firmware) that cap acceleration to ~3 units/s (~100 ms from 0→full). Measure added latency and ensure combined filtering keeps command arrival <120 ms; only raise `WATCHDOG_TIMEOUT_MS` if logs show legitimate packets landing slower. Maintain a safety margin of ≥2× worst-case filtered delay before the watchdog fires.

4. **Networking Robustness**
   - Problem: UDP dropouts trigger the watchdog after six missed frames (200 ms). Drivers feel sudden braking without warning.
   - Target: Keep 1-second rolling packet loss <5 %. Add lightweight ACK/heartbeat counters so the controller UI can show loss %, and if loss exceeds the threshold, ramp motors down smoothly instead of hard-stopping. Pace controller sends to 30 Hz with jitter <5 ms to reduce bursts.

5. **Telemetry Feedback**
   - Problem: Drivers have no real-time view of throttle state, RSSI, battery, or watchdog headroom; only console packet counters exist.
   - Target: Stream telemetry (battery voltage, RSSI, watchdog elapsed, wheel duty, trigger positions) back to the laptop via UDP or piggybacked ACKs. Display it in the controller UI with clear warnings for impending watchdog timeout (<50 ms) and packet-loss spikes. Add controller rumble / on-screen cues for severe loss or low battery.

6. **Testing & Validation**
   - Define drills (figure-eight at 50 %, rapid forward↔reverse transitions, sustained spin in place). Log joystick inputs, filtered commands, packets sent/received, watchdog trips, and wheel speeds for each run.
   - Success criteria: zero unexpected watchdog stops, curvature error <10 % vs. commanded steering, steady-state packet loss <5 %, and log-confirmed trigger-to-PWM ramp time ≈100 ms.

## Current Driving Feel
- With trigger-based direction, basic maneuvers are intuitive and reversals require only finger motion.
- Lack of expo/slew still produces twitchy responses; combined throttle+steer commands saturate quickly, so arcs feel inconsistent.
- Any Wi-Fi hiccup longer than 200 ms still causes a watchdog stop, perceived as a sudden brake with no driver warning.
- Absent telemetry keeps drivers guessing about mode, battery, or connection quality.

## Action Plan
1. Implement configurable expo curves and wheel-output normalization/calibration (controller + firmware).
2. Add dual-stage slew limiters, verify latency, and retune watchdog thresholds as needed.
3. Build a telemetry/ACK pathway so the controller UI can display packet health, watchdog margin, battery, and RSSI.
4. Execute the defined drills with logging after each change to verify targets before proceeding.

Following these concrete targets—and validating each with logged data—will move the Pico-Go LAN Robot from “fast but twitchy” to “intuitive, predictable, and competition-ready” without sacrificing the existing safety guarantees.
