# Gap Analysis

## Missing Features

- None

## Bugs

- **ONVIF Zoom Validation Error:** The `continuous_move` function was sending an improperly structured request for zoom commands, causing a "Validation constraint violation: invalid value in element 'ns2:Zoom'" error on some ONVIF-compliant cameras. The issue was traced to the use of a manually constructed dictionary that did not match the expected schema.

- **Qt Platform Plugin Issue:** The application fails to initialize the Qt platform plugin correctly on some Linux distributions. This manifests as "Could not find the Qt platform plugin xcb" errors during startup, preventing the GUI from loading.

### Proposed Solution

- **Investigate Qt Deployment:** Verify Qt plugin deployment paths and dependencies. Consider bundling required plugins with the application or implementing fallback loading mechanisms.

## Verified Functionality

- **PTZ Control Working:** The PTZ functionality has been confirmed operational using the `suds-py3` library replacement. All basic pan/tilt/zoom commands are functioning correctly with the target cameras.
- **Continuous Move Test (2025-06-18):** A test script (`ptz_test.py`) was created to verify simultaneous pan, tilt, and zoom commands using the `continuous_move` function. The test confirmed that the system can successfully execute a continuous move with `pan=0.2`, `tilt=0.2`, and `zoom=0.5` for a 5-second duration and then properly stop the movement. Log files verified the correct parameters and sequence of operations.

## Resolved Issues

- **ONVIF Zoom Validation Error:** [Resolved 2025-06-18] The `continuous_move` request payload is now built using a dictionary that correctly conforms to the ONVIF schema, and the zoom value is clamped to the valid range (`0.0` to `1.0`) before being sent. A unit test with an out-of-range zoom value has been added to `ptz_test.py` to prevent regressions.
- **ONVIF Zeep LookupError:** [Resolved 2025-06-18] The `onvif-zeep` library incompatibility was addressed by migrating to `suds-py3`. The original issue with `ContinuousMove` command validation errors no longer occurs.
