# PTZ Control Component Documentation

## Domain: PTZ Control
The PTZ (Pan-Tilt-Zoom) Control domain is responsible for translating target coordinates into physical camera movements. It ensures smooth tracking and zoom adjustment using a PID-based servo controller.

### Responsibilities
- Communicating with hardware via ONVIF (real) or simulating movements (simulated).
- Stabilizing camera motion using PID control.
- Managing camera absolute position and velocity commands.
- Handling homing logic when no targets are detected.
- Preventing servo "wind-up" by resetting integral terms during phase transitions.
- **Adaptive Gain Control**: Adjusting pan/tilt speed relative to zoom level to maintain visual tracking stability.
- **Axis Inversion**: Handling unconventional camera mounting (e.g., inverted) via software configuration.

### Related Classes
- `PTZService` ([src/ptz_controller.py](file:///home/lkless/project/code/Drone_PTZ/src/ptz_controller.py)): Handles ONVIF communication.
- `SimulatedPTZService` ([src/ptz_simulator.py](file:///home/lkless/project/code/Drone_PTZ/src/ptz_simulator.py)): Handles simulated PTZ logic.
- `PTZServo` ([src/ptz_servo.py](file:///home/lkless/project/code/Drone_PTZ/src/ptz_servo.py)): Implements PID control logic for pan and tilt.
- `PIDGains` ([src/ptz_servo.py](file:///home/lkless/project/code/Drone_PTZ/src/ptz_servo.py)): Data structure for PID tuning parameters.

### Critical Logic: Servo Reset
To maintain control loop stability, the `PTZServo` must be reset (`ptz_servo.reset()`) during the following events:
1. **Target Loss**: When the tracking phase transitions to `SEARCHING` or `LOST`.
2. **New Target**: When a new `target_id` is locked, or when first re-acquiring a target after it was lost.
3. **Internal Overlays**: When switching between IDLE and ACTIVE modes.

This prevents the integral term from carrying over errors from a previous tracking session or from periods where the camera was manually stopped or reached mechanical limits.
