# OCTAGON PLATFORM API

### HTTP COMMUNICATION PROTOCOL V2.19.

INFINITI ELECTRO-OPTICS

## Table of Contents

- Revision History......................................................................................................................................................
- 1. Overview.............................................................................................................................................................
  - 1.1. General Structure .......................................................................................................................................
  - 1.2. Interface Configuration ..............................................................................................................................
  - 1.3. Data Format................................................................................................................................................
  - 1.4. Authentication and Security.......................................................................................................................
  - 1.5. Default Credentials..................................................................................................................................
  - 1.6. Error Handling..........................................................................................................................................
  - 1.7. Device Compatibility................................................................................................................................
- 2. Command List..................................................................................................................................................
- 3. Command Details
  - 3.1. Get API Information.................................................................................................................................
  - 3.2. Get System Status....................................................................................................................................
  - 3.3. Get System Versions................................................................................................................................
  - 3.4. Get System Information
  - 3.5. Get System Time......................................................................................................................................
  - 3.6. Set System Time
  - 3.7. Get System Ethernet................................................................................................................................
  - 3.8. Set System Ethernet
  - 3.9. Get Accounts
  - 3.10. Get Account Information.....................................................................................................................
  - 3.11. Get System Temperature
  - 3.12. Hardware Restart
  - 3.13. Software Restart..................................................................................................................................
  - 3.14. Get System Presets..............................................................................................................................
  - 3.15. Get Preset By ID...................................................................................................................................
  - 3.16. Set Preset.............................................................................................................................................
  - 3.17. Clear Preset..........................................................................................................................................
  - 3.18. Go to Preset.........................................................................................................................................
  - 3.19. Stop All Preset Devices
  - 3.20. Clear All Presets...................................................................................................................................
  - 3.21. Get Devices..........................................................................................................................................
- 3.22. Get Device State
- 3.23. Re-Initialize Device
- 3.24. Get Pan-Tilt Status (Vega-Series).........................................................................................................
- 3.25. Get Pan-Tilt Position............................................................................................................................
- 3.26. Set Pan-Tilt Position.............................................................................................................................
- 3.27. Set Pan-Tilt Position (SIGMA / SENTRY Series)....................................................................................
- 3.28. Move Pan-Tilt Relative.........................................................................................................................
- 3.29. Stop Pan-Tilt
- 3.30. Move Pan-Tilt to Home Position
- 3.31. Get Pan-Tilt Configuration (Vega-Series).............................................................................................
- 3.32. Set Pan-Tilt Configuration (Vega-Series)
- 3.33. Get Pan-Tilt Configuration (LEOS-Series).............................................................................................
- 3.34. Set Pan-Tilt Configuration (LEOS-Series)
- 3.35. Get Pan-Tilt Stabilization Status
- 3.36. Set Pan-Tilt Stabilization Status...........................................................................................................
- 3.37. Get Pan-Tilt Ethernet Configuration....................................................................................................
- 3.38. Set Pan-Tilt Ethernet Configuration
- 3.39. Get Visible Lens Position
- 3.40. Set Visible Lens Position
- 3.41. Switch Visible Color Mode...................................................................................................................
- 3.42. Start Visible Auto Back-focus...............................................................................................................
- 3.43. Set Visible Digital Zoom.......................................................................................................................
- 3.44. Set Visible Digital Stabilization
- 3.45. Move Visible Lens................................................................................................................................
- 3.46. Stop Visible Lens..................................................................................................................................
- 3.47. Set Visible Fog Filter State...................................................................................................................
- 3.48. Set Visible Autofocus Mode
- 3.49. Start Visible Auto-Focus
- 3.50. Set Visible Heatwave Intensity mode..................................................................................................
- 3.51. Get Visible Configuration.....................................................................................................................
- 3.52. Set Visible Configuration
- 3.53. Get Visible Configuration (MS-Series).................................................................................................
- 3.54. Set Visible Configuration (MS-Series)..................................................................................................
- 3.55. Get Visible Camera Ethernet Configuration........................................................................................
- 3.56. Set Visible Camera Ethernet Configuration.........................................................................................
- 3.57. Get Visible Camera Ethernet Configuration (MS-Series).....................................................................
- 3.58. Set Visible Camera Ethernet Configuration (MS-Series)
- 3.59. Move Thermal Lens
- 3.60. Stop Thermal Lens...............................................................................................................................
- 3.61. Start Thermal Auto-Focus....................................................................................................................
- 3.62. Set Thermal Digital Zoom
- 3.63. Execute Thermal White Balance..........................................................................................................
- 3.64. Execute Thermal Infinity Focus............................................................................................................
- 3.65. Set Thermal Camera Digital Stabilization
- 3.66. Get Thermal Lens Position...................................................................................................................
- 3.67. Set Thermal Lens Position
- 3.68. Set Thermal Autofocus Mode..............................................................................................................
- 3.69. Get Thermal Camera Ethernet Configuration
- 3.70. Set Thermal Camera Ethernet Configuration......................................................................................
- 3.71. Get Thermal Camera Ethernet Configuration (RS-Series)
- 3.72. Set Thermal Camera Ethernet Configuration (RS-Series)....................................................................
- 3.73. Get Thermal Camera Ethernet Configuration (S-Series, NS-Series, ZS-Series)....................................
- 3.74. Set Thermal Camera Ethernet Configuration (S-Series, NS-Series, ZS-Series)
- 3.75. Get Thermal Camera Configuration (R-Series)....................................................................................
- 3.76. Set Thermal Camera Configuration (R-Series).....................................................................................
- 3.77. Get Thermal Camera Configuration (N-Series)....................................................................................
- 3.78. Set Thermal Camera Configuration (N-Series)
- 3.79. Get Thermal Camera Configuration (Z-Series)
- 3.80. Set Thermal Camera Configuration (Z-Series).....................................................................................
- 3.81. Get Thermal Camera Configuration (S-Series)
- 3.82. Set Thermal Camera Configuration (S-Series).....................................................................................
- 3.83. Get Thermal Camera Configuration (NS-Series)..................................................................................
- 3.84. Set Thermal Camera Configuration (NS-Series)...................................................................................
- 3.85. Get Thermal Camera Configuration (RS-Series)
- 3.86. Set Thermal Camera Configuration (RS-Series)...................................................................................
- 3.87. Get Thermal Camera Configuration (ZS-Series)...................................................................................
- 3.88. Set Thermal Camera Configuration (ZS-Series)
- 3.89. Get Thermal Camera Automatic NUC Configuration (Z-Series)
- 3.90. Set Thermal Camera Automatic NUC Configuration (Z-Series)...........................................................
- 3.91. Get Thermal Camera Encoding Configuration.....................................................................................
- 3.92. Set Thermal Camera Encoding Configuration
- 3.93. Get Thermal Camera OSD Configuration.............................................................................................
- 3.94. Set Thermal Camera OSD Configuration
- 3.95. Get Thermal NUC Table Status (R-Series)............................................................................................
- 3.96. Get Thermal Cooler Status (V-Series)..................................................................................................
- 3.97. Get Thermal Camera Status (Z-Series)
- 3.98. Perform Internal 1-Point NUC
- 3.99. Perform External 1-Point NUC.............................................................................................................
- 3.100. Perform Optical 1-Point NUC...............................................................................................................
- 3.101. Get OSD Menu Status..........................................................................................................................
- 3.102. Open OSD Menu..................................................................................................................................
- 3.103. Close OSD Menu..................................................................................................................................
- 3.104. Navigate OSD Menu
- 3.105. Get LRF Status......................................................................................................................................
- 3.106. Get LRF Configuration..........................................................................................................................
- 3.107. Set LRF Configuration
- 3.108. Reset LRF Configuration
- 3.109. LRF Range Request
- 3.110. Get LRF Range Request Report............................................................................................................
- 3.111. Calibrate LRF for False Alarm Rate
- 3.112. Get LRF AHRS Sample..........................................................................................................................
- 3.113. Get LRF AHRS Configuration................................................................................................................
- 3.114. Set LRF AHRS Configuration.................................................................................................................
- 3.115. Initialize LRF AHRS
- 3.116. De-initialize LRF AHRS..........................................................................................................................
- 3.117. Get ZLID Status
- 3.118. Get ZLID Intensity
- 3.119. Set ZLID Intensity.................................................................................................................................
- 3.120. Get ZLID Position
- 3.121. Set ZLID Position..................................................................................................................................
- 3.122. Start ZLID Motor..................................................................................................................................
- 3.123. Stop ZLID Motor...................................................................................................................................
- 3.124. Change ZLID Laser Mode
- 3.125. Get Search Light Configuration............................................................................................................
- 3.126. Set Search Light Configuration
- 3.127. Get Encoder Ethernet Configuration...................................................................................................
- 3.128. Set Encoder Ethernet Configuration....................................................................................................
- 3.129. Get GPS Status.....................................................................................................................................
- 3.130. Get GPS Position..................................................................................................................................
- 3.131. Get SWIR Status...................................................................................................................................
- 3.132. Get SWIR Lens Position........................................................................................................................
- 3.133. Set SWIR Lens Position
- 3.134. Get SWIR Configuration.......................................................................................................................
- 3.135. Set SWIR Configuration
- 3.136. Get SWIR Camera Encoding Configuration..........................................................................................
- 3.137. Set SWIR Camera Encoding Configuration
- 3.138. Get SWIR Camera Ethernet Configuration
- 3.139. Set SWIR Camera Ethernet Configuration...........................................................................................
- 3.140. Get SWIR Camera OSD Configuration
- 3.141. Set SWIR Camera OSD Configuration
- 3.142. Select SWIR User set............................................................................................................................
- 3.143. Save SWIR User set..............................................................................................................................
- 3.144. Get Active NUC dataset.......................................................................................................................
- 3.145. Set Active NUC dataset........................................................................................................................
- 3.146. Move SWIR Lens..................................................................................................................................
- 3.147. Start SWIR Auto-Focus.........................................................................................................................
- 3.148. Stop SWIR Lens....................................................................................................................................
- 3.149. Initialize SWIR Camera.........................................................................................................................
- 3.150. Set SWIR Camera Digital Stabilization.................................................................................................
- 3.151. Set SWIR Autofocus Mode...................................................................................................................
- 3.152. Get Modules
- 3.153. Get Module State
- 3.154. Activate / Deactivate Module..............................................................................................................
- 3.155. Get Auto Tracking Status.....................................................................................................................
- 3.156. Get Auto Tracking Configuration.......................................................................................................
- 3.157. Set Auto Tracking Configuration........................................................................................................
- 3.158. Get Auto Tracking Advanced Configuration......................................................................................
- 3.159. Set Auto Tracking Advanced Configuration.......................................................................................
- 3.160. Get Auto Tracking Device PID Configuration.....................................................................................
- 3.161. Set Auto Tracking Device PID Configuration
- 3.162. Get Auto Tracking Tracks...................................................................................................................
- 3.163. Initialize Auto Tracking Camera Device
- 3.164. Start Auto Tracking Target.................................................................................................................
- 3.165. Stop Auto Tracking Target.................................................................................................................
- 3.166. Autostart Auto Tracking Target.........................................................................................................
- 3.167. Re-Initialize Auto Tracking Device’s Track.........................................................................................
- 3.168. Clear Auto Tracking Detections.........................................................................................................
- 3.169. Set Auto Tracking Home Position......................................................................................................
- 3.170. Get HTTP Panasonic Configuration....................................................................................................
- 3.171. Get Laser Safety Status......................................................................................................................
- 3.172. Get Laser Safety Configuration..........................................................................................................
- 3.173. Set Laser Safety Configuration
- 3.174. Laser Sync
- 3.175. Get Laser Sync Configuration
- 3.176. Set Laser Sync Configuration.............................................................................................................
- 3.177. Get Lifecycle Tracker Status
- 3.178. Get Lifecycle Tracker Configuration
- 3.179. Set Lifecycle Tracker Configuration...................................................................................................
- 3.180. Pelco System Controller
- 3.181. Get Pelco System Controller Configuration.......................................................................................
- 3.182. Set Pelco System Controller Configuration
- 3.183. Send Pelco-D Commands Directly
- 3.184. Get Power Conserve Status...............................................................................................................
- 3.185. Get Power Conserve Configuration...................................................................................................
- 3.186. Set Power Conserve Configuration....................................................................................................
  - 3.187. Set Power Conserve Shutoff Time.....................................................................................................
  - 3.188. Get Processing Toggle Configuration
  - 3.189. Set Processing Toggle Configuration.................................................................................................
  - 3.190. Get TCP Pelco Receiver Configuration...............................................................................................
  - 3.191. Set TCP Pelco Receiver Configuration
  - 3.192. Get TCP Visca Keyboard Configuration..............................................................................................
  - 3.193. Get Thermal Sync Configuration........................................................................................................
  - 3.194. Set Thermal Sync Configuration
  - 3.195. Get Light Sync Configuration.............................................................................................................
  - 3.196. Set Light Sync Configuration..............................................................................................................
  - 3.197. Get Custom OSD Overlay Configuration............................................................................................
  - 3.198. Set Custom OSD Overlay Configuration
  - 3.199. Get Peripherals..................................................................................................................................
  - 3.200. Get Peripheral State
  - 3.201. Turn Defrost On / Off.........................................................................................................................
  - 3.202. Get Defrost Config.............................................................................................................................
  - 3.203. Set Defrost Configuration..................................................................................................................
  - 3.204. Get Photocell Status
  - 3.205. Get Photocell Configuration..............................................................................................................
  - 3.206. Set Photocell Configuration...............................................................................................................
  - 3.207. Turn Power Switch On / Off...............................................................................................................
  - 3.208. Get Power Switch Configuration
  - 3.209. Turn Thermal Circuit On / Off............................................................................................................
  - 3.210. Get Thermal Circuit Configuration
  - 3.211. Set Thermal Circuit Configuration
  - 3.212. Turn Washer On / Off........................................................................................................................
  - 3.213. Get Washer Configuration.................................................................................................................
  - 3.214. Set Washer Configuration
  - 3.215. Turn Wiper On / Off...........................................................................................................................
  - 3.216. Turn IR On / Off / auto.......................................................................................................................
  - 3.217. Get IR Status
- 4. Support and Custom Development...............................................................................................................
- 5. Disclaimer......................................................................................................................................................

### Revision History......................................................................................................................................................

```
Revision
Number
Notes Date
Released
```

#### 2.19.

```
Added /modules/customOsdOverlay
Added /peripherals/ir
Added /modules/lightSync
```

```
Update /devices/swir
```

```
March 06,
2023
```

## 1. Overview.............................................................................................................................................................

The Octagon HTTP API is an IP interface for accessing Ascendent and Infiniti Octagon platform devices.
This API acts as a unified point-of-contact for client software and services to access the sensors and
devices within a system. The goal is to provide consistent, logical, and reliable connectivity to our web
server(s) that exposes deep integration capabilities while simplifying interactions with our multi-faceted
architecture.

### 1.1. General Structure .......................................................................................................................................

The Octagon API branches from the base /api endpoint into four main sections that contain all major
API functionality: **system, devices, modules** , **and peripherals**
e.g. [http://192.168.1.21/api/system.](http://192.168.1.21/api/system.) The purpose of each section is described below.

```
System ─ This section covers operations concerning the underlying system and OS of the
Octagon platform, including date and time settings, system reboots, peripheral sensors, and
more.
```

```
Devices ─ The core purpose of the Octagon platform is to provide both general and specific
access to all devices on the platform. Device control, configuration, and status operations are
found here.
```

```
Modules ─ This section handles activation, configuration, and control of various modules that
extend the regular functionality of the Octagon platform. Example modules include Pelco System
Controller, Laser Sync, GPS, and Auto-Tracking. Custom features and functionality developed for
specific customers will be found here.
```

```
Peripherals ─ This makes up sensors and additions to the system. Peripherals include washers,
photocells, and defrost systems.
```

### 1.2. Interface Configuration ..............................................................................................................................

The Octagon API is only applicable via a wired ethernet connection to an Octagon-compatible system.
The API is exposed on port 80 at the given URLs.

The IP address, subnet mask, default gateway, and other network values can be configured via the
Octagon **WebPanel**. Contact Infiniti for the **WebPanel User Guide** reference document for more
information. The initial and default values for the Octagon server can be found in the **System
Configuration** document shipped with the system.

Specific wiring diagrams and pinouts will vary per system. Refer to the relevant system user manual for
this information during installation.

### 1.3. Data Format................................................................................................................................................

The default data format for all communication on the platform is JSON. All GET and POST requests
return a JSON response, including simple ‘ACK’ responses. All POST requests require properly-
formatted JSON data in the body.
Datetime values should be in the format **YYYY-MM-DDTHH:mm:ss.fff** ,
_Ex/_ **2007-11-06T16:34:41.000** (as per RFC 3339).

Time-only values should be in the format **HH:mm:ss.fff**.

JSON property names are lower camelCase; see examples under _Command List_ section.

**Successful responses** have the following format:

{
"success": true,
"data": {...}
}

The ‘data’ object can be a single value, a list of values, or another JSON object. The _Command List_
section specifies the individual command response data values.

**Error responses** have the following format:
{
"success": false,
"error": {
"code": ...,
"message": ...,
"data": {...}
}
}
**By convention, the remainder of this documentation will omit the ‘success’ property when defining
responses, as its inclusion is implied.**

### 1.4. Authentication and Security.......................................................................................................................

The Octagon API uses basic authentication via HTTP, and our high-end systems include optional HTTPS
services for encryption. As no security solution is fool-proof, we recommend pairing this API’s security
features with appropriate network security techniques.

There is no extra session information stored between API calls to this service.

The Octagon API provides basic account services for an additional layer of security.

```
Administrator ─ For system integrators and experienced users. Gives access to all public
commands, including account deletion, creation, and modification. Typical systems have one
admin account while the rest are user accounts delegated by the end-user as appropriate.
```

```
User ─ Optional. Does not allow potentially dangerous requests, including some system
configuration, system restarts, etc. By default, Infiniti provides 1 user account.
```

### 1.5. Default Credentials..................................................................................................................................

```
Account Type Username Password
Administrator admin !Inf
User user1 !Inf
```

IMPORTANT– We recommend changing the passwords to both these accounts immediately upon
configuring your system.

### 1.6. Error Handling..........................................................................................................................................

Typical API requests should return with minimal delay, assuming a reliable network environment.

Error codes and messages are contained in the HTTP responses for common errors:

```
400 ─ Bad request data, typically for POST requests
401 ─ Unauthorized
404 ─ Not found
405 ─ Used for methods not yet implemented, not supported in current version, or not
applicable to the current system environment.
500 ─ Unhandled error on the server side
```

All errors that are considered part of ‘normal operation’ will return with a status 200 response. This
occurs in cases where the request is received correctly, but the internal device or other system raised an
error. Examples are serial communication timeout, device busy, module initialization failure, data read
error, etc.
See _Data Format_ section for more information regarding error response formatting.

### 1.7. Device Compatibility................................................................................................................................

**Please note that some devices may not support all the same configuration values, commands, and
features that are listed in following sections**. The API will return an HTTP 405 error (Method Not
Allowed) for any endpoint that a given device does not support. For example, some thermal or visible
lens units will have an OSD menu that is used for configuration, so the related /config endpoint may
return a 405 error in this case.

For any POST endpoint where the data for a particular device or peripheral model differs from what is
listed here, a relevant error object may be returned with information on what fields and values were
expected. Some pantilt models, for example, may have more advanced configurations than others.

Please contact Infiniti for more information on which features the model of device in your system
supports.

## 2. Command List..................................................................................................................................................

### \* Indicates the specific URL may not be supported on all end systems and/or devices.

```
Unsupported API calls will typically return a ‘NOT SUPPORTED’ HTTP response.
```

[ ] Indicates optional query parameters.

< > Indicates mandatory query parameters.

```
Method URL Description
```

```
GET /api
Get API
information
System (/api/system)
```

```
GET /api/system
Get system
information
GET /api/system/versions List versions
GET /api/system/info List system info
GET /api/system/time Get system time
POST /api/system/time Set system time
```

```
GET /api/system/ethernet Get Octagon
ethernet info
POST /api/system/ethernet Set Octagon
ethernet
GET /api/system/accounts
Get user account
list
GET /api/system/accounts/<USERNAME>
Get a specific user
account
GET /api/system/temperature
Get temperature
readings*
```

GET /api/system?command=hardwareRestart Hardware restart

GET /api/system?command=softwareRestart Software restart

GET /api/system/presets
Get all stored
presets

GET /api/system/presets/<ID>

```
Get preset
information for
the given ID
```

#### GET

```
/api/system/presets/<ID>?
action=set[&name=<NAME>][&devices=<DEVICES>]
```

```
Set and
(optionally) name
the given preset
using the current
positions of the
given devices
```

GET /api/system/presets/<ID>?action=clear Clear the given
preset

GET /api/system/presets/<ID>?action=goto Go to the preset
with the given ID

GET /api/system/presets?action=stop

```
Convenience
endpoint to stop
all preset device
movement
```

GET /api/system/presets?action=clearAll Clear all presets

```
Devices (api/devices)
```

GET /api/devices Get device status
list

GET /api/devices/<DEVICE> Get general
device status

GET /api/devices/<DEVICE>?command=initialize

```
Run device’s
initialization
sequence
Pantilt (api/devices/pantilt)
```

GET /api/devices/pantilt/status

```
Get pan-tilt-
specific status
information*
```

GET /api/devices/pantilt/position
Get current
pan/tilt angles

POST /api/devices/pantilt/position Set (Go to)
pan/tilt angles

GET

```
/api/devices/pantilt
?command=move&direction=<DIRECTION>&speed=<SPEED>
```

```
Pantilt movement
start
```

GET /api/devices/pantilt?command=stop
Stop all
movement

GET /api/devices/pantilt?command=home
Move pan/tilt to
home position

GET /api/devices/pantilt/config
Get pantilt
configuration\*

POST /api/devices/pantilt/config
Set pantilt
configuration\*

GET /api/devices/pantilt/gyro Get gyro state\*

GET /api/devices/pantilt/gyro?enable=<true OR false>
Set gyro enable /
disable\*

GET /api/devices/pantilt/config/ethernet

```
Get pantilt
ethernet
connection
information*
```

POST /api/devices/pantilt/config/ethernet

```
Set pantilt
ethernet
connection
information*
Visible (api/devices/visible)
```

GET /api/devices/visible/position

```
Get visible lens
zoom and focus
positions
```

POST /api/devices/visible/position

```
Set visible lens
zoom and focus
positions
```

GET /api/devices/visible/config
Get visible
configuration

POST /api/devices/visible/config Set visible
configuration

GET /api/devices/visible/config/ethernet
Get ethernet
configuration

POST /api/devices/visible/config/ethernet
Set ethernet
configuration

GET /api/devices/visible?command=<MOVE COMMAND>

```
Start visible lens
zoom/focus
motors
```

GET /api/devices/visible?command=stop

```
Stop visible lens
zoom/focus
motors
```

GET

```
/api/devices/visible?command=fogFilter&enable=<true OR
false>
```

```
Enable/disable
fog filter
```

#### GET

```
/api/devices/visible?command=zoomTriggerAutofocus&
enable=<true OR false>
```

```
Turn visible lens
zoom-trigger
autofocus on or
off*
```

GET

```
/api/devices/visible?command=<day OR night OR
autoColor>Mode
```

```
Switch visible
color modes
```

GET /api/devices/visible?command=autoBackfocus

```
Executes an auto
back-focus
operation*
```

#### GET

```
/api/devices/visible?command=stabilization
&enable=<true OR false>
```

```
Set visible digital
stabilization*
```

GET /api/devices/visible?command=autofocus Execute optical
autofocus\*

GET /api/devices/visible?command=digitalZoom&mode=<MODE>
Sets the digital
zoom level\*
Thermal (api/devices/thermal)

GET /api/devices/thermal/position

```
Get thermal lens
zoom and focus
positions*
```

POST /api/devices/thermal/position

```
Set thermal lens
zoom and focus
positions*
```

GET /api/devices/thermal/config

```
Get thermal
system
configuration
```

POST /api/devices/thermal/config

```
Set thermal
system
configuration
```

GET /api/devices/thermal/config/ethernet
Get ethernet
configuration

POST /api/devices/thermal/config/ethernet
Set ethernet
configuration

GET /api/devices/thermal/config/autoNUC

```
Get automatic
internal NUC
configuration*
```

POST /api/devices/thermal/config/autoNUC

```
Set automatic
internal NUC
configuration*
```

GET /api/devices/thermal/config/encoding
Get encoding
configuration\*

POST /api/devices/thermal/config/encoding
Set encoding
configuration\*

GET /api/devices/thermal/config/osd
Get osd
configuration\*

POST /api/devices/thermal/config/osd
Set osd
configuration\*

GET /api/devices/thermal/status Get thermal
status\*

GET /api/devices/thermal/status/nuc Get nuc table
status\*

GET /api/devices/thermal/cooler/status Get cooler status\*

GET /api/devices/thermal?command=<MOVE COMMAND>

```
Start thermal
zoom/focus
motors*
```

GET /api/devices/thermal?command=stop
Stop thermal lens
motors\*

GET /api/devices/thermal?command=autofocus
Execute thermal
autofocus\*

GET /api/devices/thermal?command=digitalZoom&mode=<MODE>
Set digital zoom
mode\*

GET /api/devices/thermal?command=whiteBalance
Execute thermal
white balance\*

GET /api/devices/thermal?command=infinityFocus
Execute thermal
infinity focus\*

GET

```
/api/devices/thermal?command=stabilization
&enable=<true OR false>
```

```
Set thermal
camera digital
stabilization*
```

GET

```
/api/devices/thermal?command=zoomTriggerAutofocus
&enable=<true OR false>
```

```
Set thermal zoom
trigger autofocus*
```

GET /api/devices/thermal?command=1NUCInternal
Perform internal
1-point NUC\*

GET /api/devices/thermal?command=1NUCExternal
Perform external
1-point NUC\*

GET /api/devices/thermal?command=1NUCOptical
Perform optical 1-
point NUC\*

GET /api/devices/thermal/OSDMenu
Get OSD menu
status\*

GET /api/devices/thermal?command=openOSDMenu Open menu\*

GET /api/devices/thermal?command=closeOSDMenu Close menu\*

GET

```
/api/devices/thermal?command=navigateOSDMenu&direction=
<DIRECTION>
```

```
Navigate / select
menu options*
Laser Range Finder (api/devices/lrf)
```

GET /api/devices/lrf/status Get LRF status

GET /api/devices/lrf/config Get LRF general
configuration

POST /api/devices/lrf/config Set LRF general
configuration

GET /api/devices/lrf?command=resetConfig

```
Resets the
configuration
values of the LRF
to factory
defaults
```

GET /api/devices/lrf?command=<RANGE COMMAND>
Send a range
request

GET /api/devices/lrf?command=report<METRIC>

```
Get specific data
for a range
request
```

GET /api/devices/lrf?command=calibrate[&rate=<RATE>]
Calibrate the false
alarm rate

GET /api/devices/lrf/ahrs
Get AHRS
sample\*

GET /api/devices/lrf/ahrs/config
Get AHRS
configuration \*

POST /api/devices/lrf/ahrs/config
Set AHRS
configuration \*

GET /api/devices/lrf/ahrs?command=initialize Initialize AHRS \*

GET /api/devices/lrf/ahrs?command=deinitialize
De-initialize
AHRS \*
Zoom Laser IR Diode (api/devices/zlid)

GET /api/devices/zlid/status Get ZLID-specific
status information

GET /api/devices/zlid/intensity Get laser intensity

POST /api/devices/zlid/intensity Set laser intensity

GET /api/devices/zlid/position
Get ZLID
magnification

POST /api/devices/zlid/position
Set ZLID
magnification

GET /api/devices/zlid?command=<MOVE COMMAND>

```
Operate ZLID
magnification
motor
```

GET /api/devices/zlid?command=stop

```
Stop ZLID
magnification
motor
```

GET /api/devices/zlid?command=<on OR off>
Change laser
mode to on or off
Search Light (api/devices/searchlight)

GET /api/devices/searchlight/config Get searchlight
configuraton\*

POST /api/devices/searchlight/config Set searchlight
configuraton\*
Encoder (api/devices/encoder)

GET /api/devices/encoder/config/ethernet Get ethernet
configuration

POST /api/devices/encoder/config/ethernet Set ethernet
configuration
GPS (api/devices/gps)

GET /api/devices/gps/status Get full GPS
status data

GET /api/devices/gps/position Get GPS position
data
SWIR (api/devices/swir)

GET /api/devices/swir/status
Get SWIR-specific
status information

GET /api/devices/swir/position

```
Set SWIR lens
zoom and focus
positions
```

POST /api/devices/swir/position

```
Set SWIR lens
zoom and focus
positions
```

GET /api/devices/swir/config
Get SWIR
configuration

POST /api/devices/swir/config
Set SWIR
configuration

GET /api/devices/swir/config/encoding
Get encoding
configuration

POST /api/devices/swir/config/encoding
Set encoding
configuration

GET /api/devices/swir/config/ethernet
Get ethernet
configuration

POST /api/devices/swir/config/ethernet
Set ethernet
configuration

GET /api/devices/swir/config/osd Get osd
configuration

POST /api/devices/swir/config/osd Set osd
configuration

GET /api/devices/swir?command=<MOVE COMMAND>

```
Start SWIR
zoom/focus
motors
```

GET

```
/api/devices/swir?command=selectUserSet&mode==<userMode
command>
```

```
Selects user from
user set mode
```

GET /api/devices/swir?command=<Load/Save User set command>
Loads or Save
User set mode

GET

```
/api/devices/swir?command=setDefaultUser&user=<userMode
command>
```

```
Selects user from
user set at default
```

GET /api/devices/swir?command=autofocus
Execute SWIR
autofocus

GET /api/devices/swir?command=stop
Stop SWIR lens
motors

GET /api/devices/swir?command=initializeCamera Initializes camera

GET

```
/api/devices/swir?command=stabilization&enable=<true or
false>
```

```
Set SWIR digital
stabilization
```

GET

```
/api/devices/swir?command=zoomTriggerAutofocus&enable=<
true or false>
```

```
Set SWIR zoom
trigger autofocus
Modules (api/modules)
```

GET /api/modules
Get module
information list

GET /api/modules/<MODULE>

```
Get information
for a specific
module
```

GET /api/modules/<MODULE>?activate=<true OR false>

```
Activate or
deactivate a
module
Auto Tracking (api/modules/autoTracking)
```

GET /api/modules/autoTracking
Get base module
information

GET /api/modules/autoTracking/status Get module status

GET /api/modules/autoTracking/config
Get module
config

POST /api/modules/autoTracking/config Set module config

GET /api/modules/autoTracking/config/advanced/<DEVICE>

```
Get
detection/trackin
g config
```

POST /api/modules/autoTracking/config/advanced/<DEVICE>

```
Set
detection/trackin
g config
```

GET /api/modules/autoTracking/config/pid/<DEVICE>
Get PID PT speed
config

POST /api/modules/autoTracking/config/pid/<DEVICE>
Set PID PT speed
config

GET /api/modules/autoTracking/tracks
Get detected
tracks

GET
/api/modules/autoTracking?command=initializeDevice&came
ra=<DEVICE>

```
Activate auto
tracking on
selected camera
```

GET
/api/modules/autoTracking?
command=start&index=<INT>

```
Start tracking
object <INT>
```

GET /api/modules/autoTracking?command=stop
Stop tracking
current object

GET
/api/modules/autoTracking?
command=autoStartTrack&classify=<VALUE>

```
Autostart tracking
target
```

#### GET

```
/api/modules/autoTracking?
command=reinitialize&index=<INT>
```

```
Rerun acquisition
to optimize track
box
```

GET

```
/api/modules/autoTracking?
command=clearDetections
```

```
Clear current list
of detections
```

#### GET

```
/api/modules/autoTracking?
command=setHomePosition&zoom=<BOOL>&pantilt=<BOOL>
```

```
Set current
pantilt-zoom as
home position
Laser Safety (api/modules/laserSafety)
```

GET /api/modules/laserSafety/config

```
Get configuration
for the Laser
Safety module
```

POST /api/modules/laserSafety/config

```
Set configuration
for the Laser
Safety module
Laser Sync (api/modules/laserSync)
```

GET /api/modules/laserSync/config

```
Get configuration
for the Laser Sync
module
```

POST /api/modules/laserSync/config

```
Set configuration
for the Laser Sync
module
Life Cycle Tracker (api/modules/lifecycleTracker)
```

GET /api/modules/lifecycleTracker/config Get configuration

POST /api/modules/lifecycleTracker/config Set configuration

GET /api/modules/lifecycleTracker/status Get state data

```
Pelco System Controller (api/modules/pelcoSystemController)
```

GET /api/modules/pelcoSystemController/config

```
Get configuration
for Pelco System
Controller
```

POST /api/modules/pelcoSystemController/config

```
Set configuration
for Pelco System
Controller
```

GET /api/modules/pelcoSystemController?send=<DATA>

```
Emulate a device
by sending Pelco-
D command
Power Conserve (api/modules/powerConserve)
```

GET /api/modules/powerConserve/status Get status

GET /api/modules/powerConserve/config Get configuration

POST /api/modules/powerConserve/config Set configuration

GET

```
/api/modules/powerConserve?command=setShutoffTime&time=
<HH:MM> Set shutoff time
Processing Toggle (api/modules/processingToggle)
```

GET /api/modules/processingToggle/config Get configuration

POST /api/modules/processingToggle/config Set configuration

```
TCP Pelco Receiver (api/modules/tcpPelcoReceiver)
```

GET /api/modules/tcpPelcoReceiver/config Get configuration

POST /api/modules/tcpPelcoReceiver/config Set configuration

```
Thermal Sync (api/modules/thermalSync)
```

GET /api/modules/thermalSync/config Get configuration

POST /api/modules/thermalSync/config Set configuration

```
Light Sync (api/modules/lightSync)
```

GET /api/modules/lightSync/config Get configuration

POST /api/modules/lightSync/config Set configuration

```
Custom OSD Overlay (api/modules/customOsdOverlay)
```

GET /api/modules/customOsdOverlay/config Get configuration

POST /api/modules/customOsdOverlay/config Set configuration

```
Peripherals (api/peripherals)
```

GET /api/peripherals
Get peripheral
information list

GET /api/peripherals/<PERIPHERAL>

```
Get information
for a specific
peripheral
Deforst (api/peripherals/defrost)
```

GET

```
/api/peripherals/defrost?command=<activate OR
deactivate>
```

```
Activate/
deactivate defrost
```

GET /api/peripherals/defrost/config Get defrost
configuration

POST /api/peripherals/defrost/config Set defrost
configuration
Photocell (api/peripherals/photocell)

GET /api/peripherals/photocell/status
Get photocell
status

GET /api/peripherals/photocell/config
Get configuration
for the photocell

POST /api/peripherals/photocell/config Set configuration
for the photocell
Power Switch (api/peripherals/powerSwitch)

#### GET

```
/api/peripherals/powerSwitch?command=<activate OR
deactivate>
```

```
Activate/
deactivate power
switch
```

GET /api/peripherals/powerSwitch/config
Get power switch
configuration
Thermal Circuit (api/peripherals/thermalCircuit)

#### GET

```
/api/peripherals/thermalCircuit?command=<activate OR
deactivate>
```

```
Activate/
deactivate
thermal power
circuit
```

GET /api/peripherals/thermalCircuit/config

```
Get thermal
power circuit
configuration
```

```
POST /api/peripherals/thermalCircuit/config
```

```
Set thermal
power circuit
configuration
Washer (api/peripherals/washer)
```

#### GET

```
/api/peripherals/washer?command=<activate OR
deactivate>
&movePantilt=<true OR false>
```

```
Activate washer
```

```
GET /api/peripherals/washer/config
Get configuration
for the washer
POST /api/peripherals/washer/config Set configuration
for the washer
Wiper (api/peripherals/wiper)
```

```
GET /api/peripherals/wiper?command=<activate OR deactivate>
Activate/
deactivate wiper
IR (api/peripherals/ir)
```

```
GET /api/peripherals/ir?command=<activate OR deactivate>
Activate/
deactivate ir
```

## 3. Command Details

The following section describes the endpoints that appear in the above _Command List_. Each command is
accompanied by its URL, a description of what the command does, any data that may be required for the
command, and a valid response.

NOTE **─** Bit indices in this section represent the least significant bit, starting at 0, e.g. a bit index of 2
represents the second-rightmost bit in 10110010.

### 3.1. Get API Information.................................................................................................................................

```
URL GET /api
Comment Gets basic API information, including copyright and contact information.
Required Data None
```

NOTE – All of the following API endpoints are preceded by /api.

### 3.2. Get System Status....................................................................................................................................

```
URL GET /system
Comment Gets basic system status information.
Required Data None
```

```
Valid Response Ex/
```

```
{
"processCount": 3,
"cpuAverage": 16.95,
"cpuUsage": 16.8,
"bootTime": "2019-01-25T13:16:30.000000",
"freeRAM": "391 MB",
"upTime": "0:08:38.525663"
}
processCount─ The number of active processes in the system, which include the
main process, API process, and module processes.
```

```
cpuAverage─ The average CPU usage of the system since boot time.
```

```
cpuUsage─ The CPU usage of the system at request time.
```

```
bootTime ─ The time at which system operation began.
```

```
upTime ─ The amount of time the system has been running.
```

### 3.3. Get System Versions................................................................................................................................

```
URL GET /system/versions
Comment Gets system version information.
Required Data None
Valid Response Ex/
{
"octagon": "1.01.190401",
"project": "1.01.190328",
"webapi": "1.02.190401"
}
```

### 3.4. Get System Information

```
URL GET /system/info
Comment Returns system model, serial, and ID information.
Required Data None
Valid Response Ex/
```

```
{
"osID": "16.04",
"modelNumber": "VEGA-2075-CTZ-857-GS",
"systemSerial": "C-84001",
"octagonSerial": "ASC-12345",
```

```
"hatSerial": "ASC-12346",
```

```
}
```

### 3.5. Get System Time......................................................................................................................................

```
URL GET /system/time
Comment Gets the system time.
Required Data None
Valid Response Ex/
{
"hour": 21,
"month": 1,
"minute": 25,
"second": 46,
"year": 2019,
"day": 21
}
```

### 3.6. Set System Time

```
URL POST /system/time
Comment Sets the system time.
Required Data Format : JSON object
```

```
Parameter Expected Range Parameter
```

```
year 0 to 9999 year
month 1 to 12 month
```

```
day 1 to 31 day
hour 0 to 23 hour
minute 0 to 59 minute
second 0 to 59 second
Valid Response Standard
```

### 3.7. Get System Ethernet................................................................................................................................

```
URL GET /system/ethernet
Comment Gets the Octagon system ethernet configuration.
```

```
Required Data None.
```

```
Valid Response
```

```
Ex/
{
"address": "192.168.0.59",
"gateway": "192.168.0.1",
"subnet": "255.255.252.0"
}
```

### 3.8. Set System Ethernet

```
URL POST /system/ethernet
Comment Sets the Octagon system ethernet configuration.
Required Data Format : JSON object
```

```
Parameter Description
```

```
address The IP address of the
Octagon
subnet The subnet mask of the
Octagon
gateway
The gateway address of
the Octagon
Valid Response Standard
```

### 3.9. Get Accounts

```
URL GET /system/accounts
Comment Returns the list of accounts stored in the system.
Required Data None
Valid Response Ex/
{[
{
"username": "admin",
"type": "Administrator",
"lastRequest": "2007-11-06T16:34:41.000Z"
},
{
"username": "user1",
"type": "User",
"lastRequest": "2007-11-06T16:34:41.000Z"
},
...
]}
```

```
username ─ The username of the account
```

```
type ─ The account type, which can be either Administrator or User
```

```
lastRequest ─ The time of the last request of this user. If the user has not sent a
request, this value will be null.
```

### 3.10. Get Account Information.....................................................................................................................

```
URL GET /system/accounts/<USERNAME>
Comment Gets the account information associated with the given USERNAME.
Required Data The name of the user
Valid Response Ex/
{
"username": "user1",
"type": "User",
"lastRequest": "2007-11-06T16:34:41.000Z"
}
```

```
See Get Accounts for more information on returned data.
```

### 3.11. Get System Temperature

```
URL GET /system/temperature
Comment Gets the current temperature measured by the system. All temperatures are
returned in degrees Celsius
```

```
Ex/ /system/temperature
Required Data None
Valid Response Ex/
{
"temperature": 23.80
}
```

### 3.12. Hardware Restart

```
URL GET /system?command=hardwareRestart
```

```
Comment Performs a full reboot of the Octagon system. Note: this does not reboot camera
components.
```

```
Required Data None
Valid Response Standard
```

### 3.13. Software Restart..................................................................................................................................

```
URL GET /system?command=softwareRestart
```

```
Comment Performs a reboot of the Octagon software, which includes the core, API, and
module processes. Note: this does not reboot camera components.
Required Data None
Valid Response Standard
```

### 3.14. Get System Presets..............................................................................................................................

```
URL GET /system/presets
Comment Gets a list of all stored presets.
Required Data None
Valid Response Ex/
{
"1": {
"name": "FrontDoor",
"dateCreated": "2019-02-07T17:30:38.042",
"createdBy": "user1",
"pantilt": {
"mode": "PELCO_PRESET",
"pan": 24.203,
"tilt": -0.121
},
"visibleLens": {
"mode": "ABSOLUTE",
"zoom": 30.909,
"focus": 87.548
}
},
"3": {...},
"20": {...},
...
}
name ─ The name of the preset, which appears when a preset is set using the
name parameter of the endpoint. If no name is given, this will be null.
```

```
dateCreated ─ The date that this preset was created
```

```
createdBy ─ The API user that created this preset. If the preset was created using
a Pelco-D input device, it will be reflected here.
```

```
The pantilt , visibleLens , swirLens, zlid, and thermalLens fields will appear if their
values were stored with the preset. Their objects will include positional fields,
such as zoom and focus motor positions for each lens or pan and tilt for the pan-
tilt unit.
```

```
There is a mode parameter for each preset that identifies how the preset is stored
and called. The two possible modes are
```

- **ABSOLUTE** , in which the system uses the absolute positioning
  functionality of the device to save and recall positions, or
- **PELCO_PRESET,** where the system uses the built-in preset functionality
  of the given device.

### 3.15. Get Preset By ID...................................................................................................................................

```
URL GET /system/presets/<ID>
Comment Gets the preset information for the given ID.
Required Data The ID of the desired preset
Valid Response Ex/
{
"name": "FrontDoor",
"dateCreated": "2019-02-07T17:30:38.042",
"createdBy": "user1",
"pantilt": {
"mode": "PELCO_PRESET",
"panPosition": 24.203,
"tiltPosition": -0.121
},
"visibleLens": {
"mode": "ABSOLUTE",
"zoom": 10.909,
"focus": 87.548
}
}
```

```
See Get System Presets for more information on returned data.
```

### 3.16. Set Preset.............................................................................................................................................

#### URL GET

```
/system/presets/<ID>?action=set[&name=<NAME>][&devices=<DEVICES>]
```

```
Comment Sets and names the preset with the given ID and NAME using the current
positions of the given DEVICES.
Required Data The DEVICES parameter can be given to specify which devices will be affected by
the preset. This will be a comma-separated value field that can include the
following values:
```

- **pantilt**
- **visibleLens**
- **thermalLens**
- **swirLens**
- **zlid**
  If DEVICES is not specified, then the preset will use all above devices.

```
An optional NAME can be given to the preset.
```

```
Ex/
/system/presets/1?action=set
&name=PortEntrance&devices=pantilt,visibleLens
```

```
Valid Response Standard
```

### 3.17. Clear Preset..........................................................................................................................................

```
URL GET /system/presets/<ID>?action=clear
```

```
Comment Clears the preset with the given ID. An error message will be displayed if the
preset does not exist.
Required Data The ID of the preset to be cleared
Valid Response Standard
```

### 3.18. Go to Preset.........................................................................................................................................

```
URL GET /system/presets/<ID>?action=goto
```

```
Comment Goes to the preset with the given ID. Each device specified in the preset will
move to the stored position.
Required Data The ID of the desired preset
Valid Response Standard
```

### 3.19. Stop All Preset Devices

```
URL GET /system/presets?action=stop
```

```
Comment Convenience endpoint to stop all device movement. This only applies to devices
that may be affected by a preset, including pantilt , thermal , swir, zlid and visible.
```

```
NOTE – The move commands of some device models are uninterruptible and will
not be affected by this command.
Required Data None
Valid Response Standard
```

### 3.20. Clear All Presets...................................................................................................................................

```
URL GET /system/presets?action=clearAll
```

```
Comment Clears all stored presets. This endpoint can only be called by an Administrator -
type account.
Required Data None
Valid Response Standard
```

### 3.21. Get Devices..........................................................................................................................................

```
URL GET /devices
Comment Gets general state of all devices present on the platform.
Required Data None
Valid Response Ex/
{
"pantilt": {
"status": "CONNECTED",
"model": "VEGA",
"serialNumber": "C-56108",
"firmwareVersion": "10.02.2018"
"lastMessage": "2019-02-07T17:30:38.042"
},
"visible": {...},
"zlid": {...},
...
}
```

```
lastMessage ─ The date of the last message associated with this device that was
recorded by the system. This may be the actual last message sent to or received
from the device, or the last time the device status was updated.
```

```
serialNumber ─ The serial number of the device.
```

```
firmwareVersion ─ The firmware version of the device.
```

```
model ─ The model of the device.
```

```
The status parameter can be one of the following values:
```

```
Status Description
DISCONNECTED The device is disconnected, and no connection
attempt has been made yet.
INITIALIZING The device is establishing a connection and starting
the initialization sequence. Commands will be
ignored in this state.
CONNECTED The device is operating normally and is ready to
accept commands.
LIMITED Parts or sections of the device are operating and
communicating, but with limited or partial
functionality
```

## 3.22. Get Device State

```
URL GET /devices/<DEVICE>
Comment Gets the general state of the given DEVICE.
Required Data The name of the device
Valid Response Ex/
{
"status": "ACTIVE",
"model": "Vega",
"serialNumber": "C-56108",
"firmwareVersion": "10.02.2018"
"lastMessage": "2019-02-07T17:30:38.042"
}
```

```
See Get Devices for information on returned data.
```

## 3.23. Re-Initialize Device

```
URL GET /devices/<DEVICE>?command=initialize
```

```
Comment Performs an initialization of the given DEVICE and temporarily stops activity for
the rest of the system.
Required Data The name of the device
Valid Response Standard
```

## 3.24. Get Pan-Tilt Status (Vega-Series).........................................................................................................

```
URL GET /devices/pantilt/status
```

```
Comment
```

```
Gets the system diagnostic for the pan-tilt unit, which can be useful for
diagnosing potential problems. If you believe there is an issue with your pan-tilt
unit, record the information returned by this command and contact Infiniti for
support.
Required Data None
Valid Response Ex/
{
"boardTemperature": 24.6,
"bodyTemperature": 24.2,
"calibrationStateByte": 131,
"diagnosticsByte1": 128,
"diagnosticsByte2": 0,
"gpsAltitude": 0,
"gpsLatitude": 0,
"gpsLongitude": 0,
"gpsSatssellitesInView": 0,
"gpsTime": 0,
"internalHumidity": 26.4,
"mainLoopFrequency": 79715,
"outputStateByte": 32,
"pan": 0.007,
"panEncoderPosition": 0.007,
"panSpeed": 0.0,
"panStallGuard": 0,
"panTarget": 0.54,
"pitch": 0.62,
"platformStateByte": 4,
"roll": -0.58,
"stabilization": false,
"tilt": 0.622,
"tiltEncoderPosition": 0.002,
"tiltSpeed": 0.0,
"tiltStallGuard": 0,
"tiltTarget": 101,
"tracking": false,
"upTime": 231,
"yaw": -1.16
}
```

```
Field Name Description
boardTemperature Temperature of the system board in °C
```

bodyTemperature Temperature of the pantilt body in °C

calibrationStateByte

```
Represents the calibration state of the platform
with the following bit values:
```

```
0 : Pan optical sensor status
1 : Tilt optical sensor status
2 : Reserved
3 : Initializing
4 : Tilt calibration timeout
5 : Pan calibration timeout
6 : End sensor malfunction
7 : Calibration success
```

diagnosticsByte1

```
Represents component statuses with the following
bit values:
```

```
0-3 : Reserved
4 : Heading available
5 : GPS position available
6 : External inertial measurement unit (IMU) ready
7 : Internal IMU ready
```

diagnosticsByte2

```
More system diagnostics information, given by the
following bit values:
```

```
0-3 : Reserved
4 : Temperature protection limit exceeded
5 : Current protection limit exceeded
6 : Tilt driver error
7 : Pan driver error
```

gpsAltitude\* GPS altitude

gpsLatitude\* GPS latitude

gpsLongitude\* GPS longitude

gpsSatellitesInView\* The number of GPS satellites available

gpsTime\* GPS time in seconds

internalHumidity Internal humidity of the pantilt in percent

mainLoopFrequency
The frequency at which the board's processing
loop is running

outputStateByte

```
Represents the various output states of the device,
with 0 being "off" and 1 being "on". If bit 0 has a
value of 0, this means that output state 1 is off. If
bit 4 is 1, then output state 5 is on, and so on.
```

pan The current pan position in degrees

panEncoderPosition The pan encoder position

panSpeed The current speed of the pan motor

```
panStallGuard The stall guard for the pan motor
panTarget The target pan position
pitch* Pitchof the unit
roll* Roll of the unit
stabilization* Stabilization state
tilt The current tilt position in degrees
tiltEncoderPosition The tilt encoder position
tiltSpeed The current speed of the tiltmotor
tiltStallGuard The stall guard for the tilt motor
tiltTarget The target tilt position
tracking Whether GPS tracking is activeor not
upTime Time running this sessionin seconds
yaw* Yaw of the unit
```

## 3.25. Get Pan-Tilt Position............................................................................................................................

```
URL GET /devices/pantilt/position
Comment Gets the pan & tilt position of the device in degrees.
Required Data None
Valid Response Ex/
{
"tilt": -0.001,
"pan": 0.001
}
```

```
See Set Pan-Tilt Position for information on returned data.
```

## 3.26. Set Pan-Tilt Position.............................................................................................................................

```
URL POST /devices/pantilt/position
```

```
Comment
```

```
Sets the pan & tilt position of the device in degrees.
```

```
* Note that the tilt range is build specific.
Required Data Format: JSON object
```

```
Parameter Name Range
pan 0 to 360
```

```
tilt -90 to 90
Valid Response Standard
```

## 3.27. Set Pan-Tilt Position (SIGMA / SENTRY Series)....................................................................................

```
URL POST /devices/pantilt/position
```

```
Comment
```

```
Sets the pan & tilt position of the device in degrees with optional speed
parameter.
```

```
* Note that the tilt range is build specific.
Required Data Format: JSON object
```

```
Parameter Name Range
pan 0 to 360
tilt -90 to 90
speed (optional) 1 to 100
Valid Response Standard
```

## 3.28. Move Pan-Tilt Relative.........................................................................................................................

#### URL

#### GET

```
/devices/pantilt?command=move&direction=<DIRECTION>&[speed=<SPEED>
or tiltSpeed=<SPEED>&panSpeed=<SPEED>]
Comment Moves the pan-tilt in the specified DIRECTION, which must be one of
```

- **right**
- **left**
- **up**
- **down**
- **upright**
- **upleft**
- **downright**
- **downleft**

```
The SPEED argument must be a value between 0 and 100 and represents the
percentage of the unit's maximum speed.
```

```
The second argument can either be speed or tiltSpeed and panSpeed. If just speed
is used, both the pan and tilt speeds will be set to the given speed.
```

```
Ex/
```

```
/pantilt?command=move&direction=upright&tiltSpeed=20&panSpeed=30
```

```
Required Data None
Valid Response Standard
```

## 3.29. Stop Pan-Tilt

```
URL GET /devices/pantilt?command=stop
Comment Stops all pan-tilt motion, excluding stabilization.
Required Data None
Valid Response Standard
```

## 3.30. Move Pan-Tilt to Home Position

```
URL GET /devices/pantilt?command=home
Comment Moves the pan-tilt to its calibrated home position (pan = 0°, tilt = 0°).
Required Data None
Valid Response Standard
```

## 3.31. Get Pan-Tilt Configuration (Vega-Series).............................................................................................

```
URL GET /devices/pantilt/config
Comment Gets the pan-tilt’s current configuration values.
Required Data None
Valid Response Ex/
{
"absoluteMoveSpeed": 40.0,
"absoluteMoveRamp": 1000,
"userTiltMax": 30.0,
"relativeMoveRamp": 150,
"userTiltMin": -30.0,
"defaultPanDriftCompensation": 0.02,
"defaultTiltDriftCompensation": -0.01,
}
See Set Pan-Tilt Configuration for information on returned data.
```

## 3.32. Set Pan-Tilt Configuration (Vega-Series)

```
URL POST /devices/pantilt/config
```

```
Comment
```

```
Sets the pan-tilt’s current configuration values.
```

```
When changing software limits, please ensure the pan and tilt positions of the
unit are within these new ranges before sending the command.
```

```
Take caution when adjusting movement speed and ramps, as low ramp values
combined with high speeds can cause sudden movement and quick direction
changes, potentially damaging the unit or attached components. Contact Infiniti
for more information on safe configuration values.
```

```
*Note that the final configurable ranges for some parameters are build specific
and are generated from factory calculations specific to the model and payload.
Required Data Format : JSON object
```

```
Parameter Range Description
userTiltMin -90 to 0 Lower tilt position limit
userTiltMax 0 to 90 Upper tilt position limit
```

```
absoluteMoveSpeed 0 to 100
```

```
The move speed for
absolute positioning, given
as percentage of the unit's
max speed
```

```
absoluteMoveRamp 250 to 10,000
```

```
How quickly the unit
accelerates to max speed
during absolute movement,
measured in milliseconds
```

```
relativeMoveRamp 100 to 2,000
```

```
How quickly the unit
accelerates to max speed
during relative movement,
measured in milliseconds
```

```
defaultPanDriftCompensation -1.0 to 1.0
```

```
Degrees per second that
the pan will compensate for
gyro stabilization drift.
```

```
defaultTiltDriftCompensation -1.0 to 1.0
```

```
Degrees per second that
the tilt will compensate for
gyro stabilization drift.
Valid Response Standard
```

## 3.33. Get Pan-Tilt Configuration (LEOS-Series).............................................................................................

```
URL GET /devices/pantilt/config
Comment Gets the pan-tilt’s current configuration values.
Required Data None
Valid Response Ex/
{
```

```
"absoluteMoveSpeed": 80.0,
"absoluteMoveRamp": 2250,
"relativeMoveRamp": 350
}
See Set Pan-Tilt Configuration for information on returned data.
```

## 3.34. Set Pan-Tilt Configuration (LEOS-Series)

```
URL POST /devices/pantilt/config
```

```
Comment
```

```
Sets the pan-tilt’s current configuration values.
```

```
Take caution when adjusting movement speed and ramps, as low ramp values
combined with high speeds can cause sudden movement and quick direction
changes, potentially damaging the unit or attached components. Contact Infiniti
for more information on safe configuration values.
```

```
*Note that the final configurable ranges for some parameters are build specific
and are generated from factory calculations specific to the model and payload.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
absoluteMoveSpeed 0 to 100
```

```
The move speed for
absolute positioning, given
as percentage of the unit's
max speed
```

```
absoluteMoveRamp 2000 to 10,000
```

```
How quickly the unit
accelerates to max speed
during absolute movement,
measured in milliseconds
```

```
relativeMoveRamp 300 to 2,000
```

```
How quickly the unit
accelerates to max speed
during relative movement,
measured in milliseconds
```

```
Custom user limits are not supported on all models, and may be read-only
Valid Response Standard
```

## 3.35. Get Pan-Tilt Stabilization Status

```
URL GET /devices/pantilt/gyro
Comment Gets the status of the pan-tilt unit’s integrated stabilization system.
Required Data None
Valid Response Ex/
```

#### {

```
"active": false
}
```

## 3.36. Set Pan-Tilt Stabilization Status...........................................................................................................

```
URL GET /devices/pantilt/gyro?enable=<true OR false>
Comment Sets the status of the pan-tilt unit’s integrated stabilization system.
Required Data A value of true or false to enable or disable stabilization
Valid Response Standard
```

## 3.37. Get Pan-Tilt Ethernet Configuration....................................................................................................

```
URL GET /devices/pantilt/config/ethernet
Comment Gets the pan-tilt’s ethernet configuration information.
Required Data None
Valid Response Ex/
{
"gateway": "192.168.0.1",
"host": "192.168.0.195",
"udpPort": 3001,
"tcpPort": 3000,
"subnet": "255.255.252.0"
}
```

## 3.38. Set Pan-Tilt Ethernet Configuration

```
URL POST /devices/pantilt/config/ethernet
Comment Sets the pan-tilt’s ethernet configuration information.
Required Data Format: JSON object
```

```
Parameter Description
host The IP address of the pan-tilt
subnet The subnet mask of the pan-tilt
gateway The gateway address of the pan-tilt
```

```
tcpPort The port number (0 to 65535) that is used for TCP
communication with the pan-tilt
udpPort The port number (0 to 65535) that is used for UDP
communication with the pan-tilt
```

```
Valid Response Standard
```

## 3.39. Get Visible Lens Position

```
URL GET /devices/visible/position
Comment Gets the current zoom and focus motor positions of the lens in percent.
Required Data None
Valid Response Ex/
{
"zoom": 20.04,
"focus": 57.33
}
```

## 3.40. Set Visible Lens Position

```
URL POST /devices/visible/position
Comment Sets the zoom and focus motor positions of the visible lens in percent.
Required Data Format: JSON object
```

```
Parameter Range
zoom 0 to 100
focus 0 to 100
Valid Response Standard
```

## 3.41. Switch Visible Color Mode...................................................................................................................

```
URL GET /devices/visible?command=<day OR night OR autoColor>Mode
Comment Switches the visible camera into day (color mode), night (blackwhite mode), or
autoColor mode. The 'autoColor' is only present on select models
```

```
NOTE – This command is also sent automatically when the photocell day/night
value changes.
Required Data The camera mode to use
Valid Response Standard
```

## 3.42. Start Visible Auto Back-focus...............................................................................................................

```
URL GET /devices/visible?command=autoBackfocus
```

```
Comment Executes the camera’s auto back-focus calibration procedure. This procedure can
take up to 10 seconds or more, during which the camera or lens cannot be
operated.
```

```
NOTE – This command is typically only used after a visible lens extender is
toggled on or off. For all other use-cases, Infiniti will factory calibrate the
camera’s back-focus and it should not need initial or ongoing adjustment.
Required Data None
Valid Response Standard
```

## 3.43. Set Visible Digital Zoom.......................................................................................................................

```
URL GET /devices/visible?command=digitalZoom&mode=<MODE>
```

```
Comment Sets the digital zoom mode based on the given MODE, the MODE will be an
integer in a range specific to the visible series.
Required Data The MODE integer
Valid Response Standard
```

## 3.44. Set Visible Digital Stabilization

```
URL GET /devices/visible?command=stabilization&enable=<true OR
false>
Comment Activate or deactivate the digital stabilization function on the visible camera
Required Data A value of true or false to enable or disable stabilization
Valid Response Standard
```

## 3.45. Move Visible Lens................................................................................................................................

```
URL GET /devices/visible?command=<MOVE COMMAND>
Comment Starts the zoom or focus motors depending on the given MOVE COMMAND,
which can be one of the following:
```

```
Command Description
```

```
zoomTele Starts the zoom motor in the
tele direction.
zoomWide Starts the zoom motor in the
wide direction.
```

```
focusFar
```

```
Starts the focus motor in the far
direction.
```

```
focusNear
```

```
Starts the focus motor in the
near direction.
```

```
Required Data The COMMAND string
Valid Response Standard
```

## 3.46. Stop Visible Lens..................................................................................................................................

```
URL GET /devices/visible?command=stop
Comment Stops both zoom and focus motors of the visible lens.
Required Data None
Valid Response Standard
```

## 3.47. Set Visible Fog Filter State...................................................................................................................

```
URL GET /devices/visible?command=fogFilter&enable=<true OR false>
Comment Sets the state of the fog filter.
Required Data Either true or false to enable or disable the fog filter
Valid Response Standard
```

## 3.48. Set Visible Autofocus Mode

```
URL GET /devices/visible?command=zoomTriggerAutofocus&enable=<true
OR false>
```

```
Comment
```

```
Sets the lens’ autofocus mode. If enabled, the lens will perform an autofocus
whenever zooming has stopped. When inactive, the autofocus command must be
called manually.
Required Data Either true or false to enable or disable zoom-trigger autofocus.
Valid Response Standard
```

## 3.49. Start Visible Auto-Focus

```
URL GET /devices/visible?command=autofocus
Comment Execute an auto-focus sequence with the visible lens.
Required Data None
Valid Response Standard
```

## 3.50. Set Visible Heatwave Intensity mode..................................................................................................

```
URL GET /devices/visible?command=heatWaveIntensity&mode=<mode>
```

```
Comment
```

```
Sets the Lens’s Dewave Intensity depending on the mode selected. Command
heatwave intensity must called be manually.
mode Description
Low Sets Dewave intensity to low frequency
Middle Sets Dewave intensity to medium frequency
High Sets Dewave intensity to high frequency
```

```
Note that, this option may not available, depending on device support feature.
Required Data None
Valid Response Standard
```

## 3.51. Get Visible Configuration.....................................................................................................................

```
URL GET /devices/visible/config
Comment Gets the camera’s current configuration values
Required Data None
Valid Response Ex/
{
"stabilizing": false,
"colorMode": "AUTO",
"processingMode": "OFF",
"autofocusMode": "ZOOM_TRIGGER",
"fogFilter": false,
"extender": true
}
```

```
Note that processingMode , stabilizing , fogFilter , and extender may not be
available, depending on model’s supported features.
```

## 3.52. Set Visible Configuration

```
URL POST /devices/visible/config
Comment Sets the thermal camera’s current configuration values.
Required Data None
Valid Response Format : JSON object
```

```
Parameter Range Description
```

```
autofocusMode MANUAL, AUTO, or
ZOOM_TRIGGER
```

```
Sets the autofocus
execution mode
```

```
colorMode
```

#### AUTO,

```
BLACKWHITE, or
COLOR
```

```
Sets the active color
mode*
```

```
extender true or false If the 2x extender is
activated
focusMode MANUAL or
DISABLED
Set focus control mode
```

```
focusSpeed 1 to 7 Speed of focus actions
```

```
fogFilter true or false
```

```
Activate fog filter. For
some models, fogFilter is
also changes to black-
white.
gamma 0 to 15 Set gamma
```

```
processingMode BLC, HLC, OFF, or
WDR
```

```
Sets the active image
processing mode
sharpening 0 to 15 Set sharpening
```

```
stabilizing false or true If electronic stabilization
is enabled (DIS, EIS)
zoomSpeed 1 to 7 Speed of zoom actions
2dnr 0 to 100 Set 2D noise reduction
3dnr 0 to 255 Set 3D noise reduction
```

```
Note that colorMode, processing mode , stabilizing , fogFilter , extender,
focusMode, focusSpeed, zoomSpeed, gamma, sharpening, 2dnr, and 3dnr may
not be available, depending on model’s supported features.
```

```
*colorMode option AUTO is not available on all models.
*autofocusMode option AUTO is not available on all models.
```

## 3.53. Get Visible Configuration (MS-Series).................................................................................................

```
URL GET /devices/visible/config
Comment Gets the camera’s current configuration values
Required Data None
Valid Response Ex/
{
"2dnr": 0,
"3dnr": 0,
"autofocusMode": "ZOOM_TRIGGER",
"autogainMax": 0,
```

```
"autogainMaxExp": 255,
"autogainMin": 0,
"autogainMinExp": 0,
"autogainMinRange": 0,
"autogainMode": "AUTO",
"autogainROISize": 100,
"autogainUpdateRate": 32,
"brightness": 128,
"contrast": 128,
"denoise": 0,
"denoiseMask": "NONE",
"enhancement": "NONE",
"enhancementBlend": 255,
"enhancementStrength": 20,
"focusSpeed": 6,
"fogFilter": false,
"gamma": 4,
"gaussianBlur": 0,
"hue": 0,
"lapMinDiff": 0,
"osdEnabled": false,
"rejectBrightTail": 0,
"rejectDarkTail": 0,
"saturation": 128,
"sharpening": 0,
"stabilizing": false,
"zoomSpeed": 5
}
```

## 3.54. Set Visible Configuration (MS-Series)..................................................................................................

```
URL POST /devices/visible/config
Comment Sets the thermal camera’s current configuration values.
Required Data None
Valid Response Format : JSON object
```

```
Parameter Range Description
2dnr 0 to 100 Set 2D noise reduction
3dnr 0 to 255 Set 3D noise reduction
```

autofocusMode

#### MANUAL,

#### ZOOM_TRIGGER,

```
or OFF
```

```
Auto focus after zooming, or
only manual control
```

autogainMax 0 to 65535 Max value of image pixel
data for AGC calculations

autogainMaxExp 0 to 255 Max exposure or integration
time

autogainMin 0 to 65535 Min value of image pixel
data for AGC calculations

autogainMinExp 0 to 255 Min exposure or integration
time

autogainMinRange 0 to 65535

```
Forces the AGC max/min
spread to be at least this
value
```

autogainMode AUTO, MANUAL Mode used to apply
autogain calculations

autogainROISize 25 to 100

```
Region of Interest as
percent of scene for AGC
algorithm
```

autogainUpdateRate 1 to 255 Rate at which AGC max/min
are updated

brightness 0 to 255 Video brightness level

contrast 0 to 255 Video contrast level

denoise 0 to 255

```
Reduce impact of noisy
pixels through video
processing algorithms
```

denoiseMask

#### NONE, AERIAL,

#### STARING

```
Turbulence-mitigation video
processing algorithms
```

enhancement

#### NONE, CLAHE,

```
LAP, CLAHE9-bit,
CLAHE10-bit
```

```
Improve image quality by
various video processing
algorithms
```

enhancementBlend 0 to 255

```
Blend of fully enhanced
video with unprocessed
video. Higher value = more
enhancement
```

enhancementStrength 0 to 127 Strength of video
enhancement algorithm

focusSpeed 1 to 7 Speed of focus motors

fogFilter true or false

```
Activate fog filter. For some
models, fogFilter is also
changes to black-white.
```

gamma 0 to 15 Set gamma

gaussianBlur 0 to 13 Blur strength to the image

hue 0 to 255 Video hue level

```
lapMinDiff 0 to 13 LAP adjustment
```

```
rejectBrightTail 0 to 255
```

```
Reject this precent
(value/10) of the left side of
autogain histogram
```

```
rejectDarkTail 0 to 255
```

```
Reject this precent
(value/10) of the right side
of autogain histogram
sharpening 0 to 15 Set sharpening
```

```
stabilizing true or false Toggle digital stabilization
feature
zoomSpeed 1 to 7 Speed of zoom motors
```

## 3.55. Get Visible Camera Ethernet Configuration........................................................................................

```
URL GET /devices/visible/config/ethernet
Comment Gets the visible camera’s ethernet configuration information, if applicable
Required Data None
Valid Response Ex/
{
"host": "192.168.0.180",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1",
"port": 80,
"username": "admin",
"password": "admin",
"limited": false
}
```

## 3.56. Set Visible Camera Ethernet Configuration.........................................................................................

```
URL POST /devices/visible/config/ethernet
Comment Sets the visible camera’s ethernet configuration information.
Required Data Only admin accounts can set ethernet configuration.
```

```
IPv4 network configuration data matching the format in the example above. Note
that the username and password must match the corresponding device’s web
client. Consult an Infiniti technician for more information.
```

```
password is only visible to admin accounts.
```

```
limited parameter is not required. limited indicates unsuccessful ethernet
connection to device, suggesting network configuration data is incorrect.
```

```
Valid Response Standard
```

## 3.57. Get Visible Camera Ethernet Configuration (MS-Series).....................................................................

```
URL GET /devices/visible/config/ethernet
```

```
Comment
```

```
Gets the visible camera’s ethernet configuration information, if applicable. limited
indicates unsuccessful ethernet connection to device, suggesting network
configuration data is incorrect.
Required Data None
Valid Response Ex/
{
"host": "192.168.0.179",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1".
"recvPort": 14002,
"sendPort": 14001,
"octagonAddress": "192.168.0.239",
"limited": false,
}
```

## 3.58. Set Visible Camera Ethernet Configuration (MS-Series)

```
URL POST /devices/visible/config/ethernet
Comment Sets the visible camera’s ethernet configuration information.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
host IPv4 valid address
Address of the thermal
system
subnet
IPv4 valid subnet
mask Subnet Mask
gateway IPv4 valid address
Address of gateway
router
```

```
recvPort 1 to 65535
```

```
Port that the Octagon
system will receive data
from the thermal device
```

```
sendPort 1 to 65535
```

```
Port that the Octagon
system will send data to
the thermal device
```

```
octagonAddress IPv4 valid address
```

```
This address can either
be set to current
Octagon address or the
```

```
secondary static
60.61.62.60.
Valid Response Standard
```

## 3.59. Move Thermal Lens

#### URL GET

```
/devices/thermal?command=<MOVE COMMAND>
Comment Moves the thermal lens’ zoom or focus motors in the specified direction.
```

```
Command Description
zoomTele Startsthe zoom motor in the tele direction.
zoomWide Starts thezoom motor in the wide direction.
focusFar Starts the focus motor in the far direction.
focusNear Starts thefocus motor in the near direction.
Ex/
/devices/thermal?command=zoomTele
```

```
Required Data The COMMAND string
Valid Response Standard
```

## 3.60. Stop Thermal Lens...............................................................................................................................

```
URL GET /devices/thermal?command=stop
Comment Stops both zoom and focus motors of the thermal lens.
Required Data None
Valid Response Standard
```

## 3.61. Start Thermal Auto-Focus....................................................................................................................

```
URL GET /devices/thermal?command=autofocus
Comment Executes an auto-focus sequence with the thermal lens.
Required Data None
Valid Response Standard
```

## 3.62. Set Thermal Digital Zoom

```
URL GET /devices/thermal?command=digitalZoom&mode=<MODE>
```

```
Comment Sets the digital zoom mode based on the given MODE, the MODE will be an
integer in a range specific to the thermal series.
Required Data The MODE integer
Valid Response Standard
```

## 3.63. Execute Thermal White Balance..........................................................................................................

```
URL GET /devices/thermal?command=whiteBalance
Comment Executes a white balancing operation.
Required Data None
Valid Response Standard
```

## 3.64. Execute Thermal Infinity Focus............................................................................................................

```
URL GET /devices/thermal?command=infinityFocus
Comment Moves the focus motor to infinity focus position for the current FOV.
Required Data None
Valid Response Standard
```

## 3.65. Set Thermal Camera Digital Stabilization

```
URL GET /devices/thermal?command=stabilization&enable=<true OR
false>
Comment Activate or deactivate the digital stabilization function on the thermal camera
Required Data A value of true or false to enable or disable stabilization
Valid Response Standard
```

## 3.66. Get Thermal Lens Position...................................................................................................................

```
URL GET /devices/thermal/position
Comment Gets the zoom and focus positions of the thermal lens in percentage.
Required Data None
Valid Response Ex/
{
```

```
"zoom": 53.502,
"focus": 48.819
}
```

## 3.67. Set Thermal Lens Position

```
URL POST /devices/thermal/position
Comment Set the zoom and focus positions of the thermal lens in percent.
Required Data Format : JSON object
```

```
Parameter Range
zoom 0 to 100
focus 0 to 100
Valid Response Standard
```

## 3.68. Set Thermal Autofocus Mode..............................................................................................................

```
URL GET /devices/thermal?command=zoomTriggerAutofocus&enable=<true
OR false>
```

```
Comment
```

```
Sets the lens’ autofocus mode. If enabled, the lens will perform an autofocus
whenever zooming has stopped. When inactive, the autofocus command must be
called manually.
Required Data Either true or false to enable or disable zoom-trigger autofocus.
Valid Response Standard
```

## 3.69. Get Thermal Camera Ethernet Configuration

```
URL GET /devices/thermal/config/ethernet
```

```
Comment
```

```
Gets the thermal camera’s ethernet configuration information. limited indicates
unsuccessful ethernet connection to device, suggesting network configuration
data is incorrect.
Required Data None
Valid Response Ex/
{
"host": "192.168.0.180",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1",
"port": 80,
"username": "admin",
"password": "admin",
```

```
"limited": false
}
```

## 3.70. Set Thermal Camera Ethernet Configuration......................................................................................

```
URL POST /devices/thermal/config/ethernet
Comment Sets the thermal camera’s ethernet configuration information.
Required Data Only admin accounts can set ethernet configuration.
```

```
IPv4 network configuration data matching the format in the example above. Note
that the username and password must match the corresponding device’s web
client. Consult an Infiniti technician for more information.
```

```
password is only visible to admin accounts.
```

```
limited parameter is not required. limited indicates unsuccessful ethernet
connection to device, suggesting network configuration data is incorrect.
```

```
Valid Response Standard
```

## 3.71. Get Thermal Camera Ethernet Configuration (RS-Series)

```
URL GET /devices/thermal/config/ethernet
Comment Gets the thermal camera’s ethernet configuration information.
Required Data None
Valid Response Ex/
{
"engine":
"host": "60.61.62.62",
"subnet": "255.255.252.0",
"gateway": "60.61.62.1",
"recvPort": 14002,
"sendPort": 14001,
"octagonAddress": "60.61.62.60"
,
"sensor":
"host": "60.61.62.61",
"subnet": "255.255.252.0",
"gateway": "60.61.62.1",
"port": 9
}
```

## 3.72. Set Thermal Camera Ethernet Configuration (RS-Series)....................................................................

```
URL POST /devices/thermal/config/ethernet
Comment Sets the thermal camera’s ethernet configuration information.
Required Data IPv4 network configuration data matching the format in the example above.
```

```
Valid Response Standard
```

## 3.73. Get Thermal Camera Ethernet Configuration (S-Series, NS-Series, ZS-Series)....................................

```
URL GET /devices/thermal/config/ethernet
```

```
Comment
```

```
Gets the thermal camera’s ethernet configuration information. limited indicates
unsuccessful ethernet connection to device, suggesting network configuration
data is incorrect.
Required Data None
Valid Response Ex/
{
"host": "192.168.0.179",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1".
"recvPort": 14002,
"sendPort": 14001,
"octagonAddress": "192.168.0.239",
"limited": false,
}
```

## 3.74. Set Thermal Camera Ethernet Configuration (S-Series, NS-Series, ZS-Series)

```
URL POST /devices/thermal/config/ethernet
Comment Sets the thermal camera’s ethernet configuration information.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
host IPv4 valid address
Address of the thermal
system
subnet
IPv4 valid subnet
mask
Subnet Mask
```

```
gateway IPv4 valid address Address of gateway
router
```

```
recvPort 1 to 65535
```

```
Port that the Octagon
system will receive data
from the thermal device
```

```
sendPort 1 to 65535
```

```
Port that the Octagon
system will send data to
the thermal device
```

```
octagonAddress IPv4 valid address
```

```
This address can either
be set to the
configurable octagon
address or the secondary
static 60.61.62.60.
Valid Response Standard
```

## 3.75. Get Thermal Camera Configuration (R-Series)....................................................................................

```
URL GET /devices/thermal/config
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
"autofocusMode": "MANUAL",
"digitalZoom": 1,
"focusSpeed": 4,
"targetEnabled": false,
"zoomSpeed": 3,
"imageLevel": {
"gamma": 15,
"gain": 0,
"offset": 0
},
"nuc": {
"nucTable": 2,
"nucSettingMode": "AUTO",
"defaultNUCTable": 4
},
"palette": {
"colorPalette": -1,
"defaultColorPalette": -1,
"whiteHot": true
},
"processing": {
"enhancement": "LOW",
```

```
"histogramLevel": "LOW",
"sharpening": "OFF",
"spatialFilter": "HIGH",
"temporalFilter": "HIGH"
}
}
```

```
See Set Thermal Camera Configuration (R-Series) for information on returned data.
```

## 3.76. Set Thermal Camera Configuration (R-Series).....................................................................................

```
URL POST /devices/thermal/config
```

```
Comment
```

```
Sets the thermal camera’s current configuration values.
```

```
*For manual NUC table setting, the nucSettingMode must be MANUAL.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
autofocusMode MANUAL or
ZOOM_TRIGGER
```

```
Auto focus after
zooming, or only manual
control
digitalZoom 1, 2, 4, or 5 Digital zoom level
focusSpeed 3 to 6 Speed of focus actions
targetEnabled true or false On screen target
zoomSpeed 1 to 6 Speed of zoom actions
imageLevel
gamma -128to 127 Image processing
gain -128 to 127 Image processing
offset -128 to 127 Image processing
nuc
nucTable 0 to 5 Current NUC table
```

```
nucSettingMode AUTO or MANUAL
```

```
MANUAL allows for
manual selection of NUC
tables, AUTO uses the
NUC selected by the
thermal based on the
current image
defaultNUCTable 0 to 5
NUC table the system
will start in
```

```
palette
```

```
colorPalette -1 to 8
Index of the active color
palette
```

```
defaultColorPalette -1 to 8
```

```
Color palette the system
initializes into and when
the color palette reset
preset is used
whiteHot true or false Polarity
processing
```

```
enhancement
OFF, LOW, MED, or
HIGH Image processing
histogramLevel
OFF, LOW, MED, or
HIGH Image processing
sharpening
OFF, LOW, MED, or
HIGH Image processing
spatialFilter OFF, LOW, MED, or
HIGH
Image processing
```

```
temporalFilter OFF, LOW, MED, or
HIGH
Image processing
```

```
Valid Response Standard
```

## 3.77. Get Thermal Camera Configuration (N-Series)....................................................................................

```
URL GET /devices/thermal/config
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
"AGLCBrightness": 0,
"AGLCContrast": 256,
"AGLCMode": "HISTOGRAM",
"LAPBackground": 16384,
"LAPFilter": true,
"LAPForeground": 850,
"activeNUCTable": 3,
"autofocusMode": "MANUAL",
"colorPalette": 0,
"continuousAutofocusMode": false,
"digitalZoom": 1,
"focusSpeed": 3,
"histogramROIIndex": 0,
"noiseFilterMode": "OFF",
"polarity": "WHITEHOT",
```

```
"statisticsOverlay": true,
"zoomSpeed": 3
}
```

```
See Set Thermal Camera Configuration (N-Series) for information on returned data.
```

## 3.78. Set Thermal Camera Configuration (N-Series)

```
URL POST /devices/thermal/config
Comment Sets the thermal camera’s current configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
AGLCBrightness -32768 to 32767
```

```
AGLC brightness value
applied while in
MANUAL AGLC mode
```

```
AGLCContrast 0 to 65535
```

```
AGLC contrast value
applied while in
MANUAL AGLC mode
```

```
AGLCMode
```

```
One of
```

- Off
- Manual
- Linear
- Histogram
- GammaRemap

```
AGLC (Automatic Gain
and Level Control) mode
for the analog output
```

```
LAPBackground 0 to 50,000 LAP Background value
```

```
LAPFilter true or false
```

```
Enable/disable the LAP
DCE filter (Local Area
Processing Dynamic
Contrast Enhancement).
LAPForeground 0 to 50,000 LAP foreground value
```

```
activeNUCTable 0 to 5
```

```
Select the active thermal
NUC table index. Note
that some systems may
support different index
ranges.
```

```
autofocusMode
ZOOM_TRIGGER or
MANUAL
```

```
Run autofocus after each
zoom command finishes,
or only on manual
command
colorPalette 0 to 13 Index of the active color
palette
continuousAutofocusMode true or false Toggle autofocus mode
digitalZoom 1, 2, or 4 Digital zoom intensity
```

```
focusSpeed 0 to 4 Focus motor speed
```

```
histogramROIIndex 0 to 7
Region of interest for
histogram calculations
```

```
noiseFilterMode
```

```
One of
```

- Disabled
- Median3x3
- Gaussian3x3
- Gaussian5x5

```
Noise filter mode
```

```
polarity
```

```
One of
```

- WhiteHot
- BlackHot

```
Thermal image colour
polarity. Actual colors
depend on the active
color palette.
```

```
statisticsOverlay true or false
```

```
Toggle the sensor
statistics overlay on or
off
zoomSpeed 0 to 4 Zoom motor speed
Valid Response Standard
```

## 3.79. Get Thermal Camera Configuration (Z-Series)

```
URL GET /devices/thermal/config
```

```
Comment
```

```
Gets the thermal’s current configuration values.
```

```
zoomSpeed and/or focusSpeed and/or autofocusMode will not be shown if on a
fixed lens system.
Required Data None
Valid Response Ex/
{
"AGLCBrightness": 256,
"AGLCContrast": 128,
"AGLCMode": "AUTO_0",
"DICEEnabled": true,
"DICELevel": 4,
"autofocusMode": "ZOOM_TRIGGER",
"automaticShutter": true,
"colorPalette": "WHITE_HOT",
"digitalZoom": "1",
"focusSpeed": 10,
"noiseFilter": true,
"zoomSpeed": 10
}
```

```
See Set Thermal Camera Configuration (Z-Series) for information on returned data.
```

## 3.80. Set Thermal Camera Configuration (Z-Series).....................................................................................

```
URL POST /devices/thermal/config
```

```
Comment
```

```
Sets the thermal camera’s current configuration values.
```

```
zoomSpeed and/or focusSpeed and/or autofocusMode are not required if on a
fixed lens system.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
AGLCBrightness 1 to 512 Adjusts the brightness
for manual AGLC mode.
AGLCContrast 1 to 256 Adjusts the contrast for
manual AGLC mode.
AGLCMode AUTO_0, AUTO_1, or
MANUAL
```

```
Automatic Gain Level
Control
DICEEnabled true or false Enable/disable DICE
```

```
DICELevel 1 to 8 Adjusts the intensity of
the DICE processing
```

```
autofocusMode
MANUAL or
ZOOM_TRIGGER
```

```
Auto focus after
zooming, or only manual
control
automaticShutter true or false Also configurable via
/config/autoNUC
```

```
colorPalette
```

#### BLACK_HOT, ICE_FIRE,

#### RAINBOW, SEPID,

```
WARNING_RED or
WHITE_HOT
```

```
Name of active color
palette
```

```
digitalZoom 1, 2, 4, or 8 Digital zoom intensity
focusSpeed 10 to 32 Thermal focus speed
```

```
noiseFilter true or false Enable noise filter
processing
zoomSpeed 10 to 32 Thermal zoom speed
Valid Response Standard
```

## 3.81. Get Thermal Camera Configuration (S-Series)

```
URL GET /devices/thermal/config
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
```

```
"autofocusChangePercent": 4.0,
"autofocusMode": "MANUAL",
"autofocusROISize": 42,
"autofocusRateAdjust": 100,
"autogainMax": 32850,
"autogainMin": 32740,
"autogainMinRange": 0,
"autogainMode": "AUTO",
"autogainROISize": 100,
"autogainUpdateRate": 32,
"brightness": 75,
"colorPalette": "DEFAULT",
"contrast": 65,
"denoise": 0,
"denoiseMask": "NONE",
"digitalZoom": "1",
"enhancement": "CLAHE",
"enhancementBlend": 200,
"enhancementStrength": 7,
"focusSpeed": 80,
"osdEnabled": false,
"polarity": "DEFAULT",
"saturation": 128,
"sharpen": 5,
"stabilizing": false,
"zoomSpeed": 40
}
See Set Thermal Camera Configuration (S-Series) for information on returned data.
```

## 3.82. Set Thermal Camera Configuration (S-Series).....................................................................................

```
URL POST /devices/thermal/config
Comment Sets the thermal camera’s current configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
autofocusChangePercent 0.00 to 25.00
Percentage change required
before direction change
```

```
autofocusMode
```

#### MANUAL,

#### ZOOM_TRIGGER,

```
or OFF
```

```
Auto focus after zooming, or
only manual control
```

```
autofocusROISize 5 to 100
```

```
Region of Interest as
percent of scene for
autofocus algorithm
```

autofocusRateAdjust 0 to 1000 Speed of focus adjustment
during autofocus

autogainMode AUTO, MANUAL Mode used to apply
autogain calculations

autogainMax 0 to 65535 Max value of image pixel
data for AGC calculations

autogainMin 0 to 65535 Min value of image pixel
data for AGC calculations

autogainROISize 25 to 100

```
Region of Interest as
percent of scene for AGC
algorithm
```

autogainMinRange 0 to 65535

```
Forces the AGC max/min
spread to be at least this
value
```

autogainUpdateRate 1 to 255 Rate at which AGC max/min
are updated

brightness 0 to 255 Video brightness level

colorPalette

#### NONE, DEFAULT,

#### RAINBOW, IRON,

#### HOTCOLD, JET

```
False color palette
```

contrast 0 to 255 Video contrast level

denoise 0 to 255

```
Reduce impact of noisy
pixels through video
processing algorithms
```

denoiseMask

#### NONE, AERIAL,

#### STARING

```
Turbulence-mitigation video
processing algorithms
```

digitalZoom 1, 1.5, 2, 3, 4

```
Artificial zoom effect by
cropping and inflating pixels
digitally
```

enhancement

#### NONE, CLAHE,

```
LAP, CLAHE9-bit,
CLAHE10-bit
```

```
Improve image quality by
various video processing
algorithms
```

enhancementBlend 0 to 255

```
Blend of fully enhanced
video with unprocessed
video. Higher value = more
enhancement
```

enhancementStrength 0 to 127
Strength of video
enhancement algorithm

focusSpeed 0 to 100 Speed of focus motors

gaussianBlur 0 to 13 Blur strength to the image

lapMinDiff 0 to 13 LAP adjustment

osdEnabled true or false

```
Toggle on-screen text
overlay. Also accessible at
/api/thermal/config/osd
```

```
polarity
```

#### DEFAULT,

#### INVERTED

```
Switches the thermal colors
displayed as hot and cold.
Example: Switch from
white=hot to black=hot
sharpen 0 to 15
Level of sharpening
algorithm applied to image
stabilizing true or false
Toggle digital stabilization
feature
zoomSpeed 0 to 100 Speed of zoom motors
Valid Response Standard
```

## 3.83. Get Thermal Camera Configuration (NS-Series)..................................................................................

```
URL GET /devices/thermal/config
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
"AGLCBrightness": 0,
"AGLCContrast": 256,
"AGLCMode": "HISTOGRAM",
"LAPBackground": 16384,
"LAPFilter": true,
"LAPForeground": 850,
"activeNUCTable": 3,
"autofocusMode": "MANUAL",
"autogainMax": 0,
"autogainMaxExp": 255,
"autogainMin": 0,
"autogainMinExp": 0,
"autogainMinRange": 147,
"autogainMode": "AUTO",
"autogainROISize": 100,
"autogainUpdateRate": 1,
"brightness": 120,
"colorPalette": 0,
"continuousAutofocusMode": false,
"contrast": 160,
"denoise": 0,
"denoiseMask": "NONE",
"digitalZoom": 1,
"enhancement": "CLAHE",
"enhancementBlend": 255,
"enhancementStrength": 6,
```

```
"focusSpeed": 3,
"gaussianBlur": 0,
"histogramROIIndex": 0,
"hue": 254,
"lapMinDiff": 0,
"noiseFilterMode": "OFF",
"osdEnabled": true,
"polarity": "WHITEHOT",
"rejectBrightTail": 0,
"rejectDarkTail": 0,
"sharpen": 4,
"stabilizing": false,
"statisticsOverlay": true,
"zoomSpeed": 3
}
```

```
See Set Thermal Camera Configuration (NS-Series) for information on returned data.
```

## 3.84. Set Thermal Camera Configuration (NS-Series)...................................................................................

```
URL POST /devices/thermal/config
Comment Sets the thermal camera’s current configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
AGLCBrightness -32768 to 32767
```

```
AGLC brightness value
applied while in MANUAL
AGLC mode
```

```
AGLCContrast 0 to 65535
```

```
AGLC contrast value applied
while in MANUAL AGLC
mode
```

```
AGLCMode
```

#### OFF, MANUAL,

#### LINEAR,

#### HISTOGRAM,

#### GAMMAREMAP

```
AGLC (Automatic Gain and
Level Control) mode for the
analog output
```

```
LAPBackground 0 to 50,000 LAP Background value
```

```
LAPFilter true or false
```

```
Enable/disable the LAP DCE
filter (Local Area Processing
Dynamic Contrast
Enhancement).
LAPForeground 0 to 50,000 LAP foreground value
```

```
activeNUCTable 0 to 5
```

```
Select the active thermal
NUC table index. Note that
some systems may support
different index ranges.
```

autofocusMode MANUAL,
ZOOM_TRIGGER

```
Auto focus after zooming, or
only manual control
```

autogainMax 0 to 65535 Max value of image pixel
data for AGC calculations

autogainMaxExp 0 to 255 Maximum exposure or
integration time

autogainMin 0 to 65535 Min value of image pixel
data for AGC calculations

autogainMinExp 0 to 255
Minimum exposure or
integration time

autogainMinRange 0 to 65535

```
Forces the AGC max/min
spread to be at least this
value
```

autogainMode AUTO, MANUAL
Mode used to apply
autogain calculations

autogainROISize 25 to 100

```
Region of Interest as
percent of scene for AGC
algorithm
```

autogainUpdateRate 1 to 255
Rate at which AGC max/min
are updated

brightness 0 to 255 Video brightness level

colorPalette 0 to 13 Index of the active color
palette

continuousAutofocusMode true or false Toggle continuous
autofocus feature

contrast 0 to 255 Video contrast level

denoise 0 to 255

```
Reduce impact of noisy
pixels through video
processingalgorithms
```

denoiseMask

#### NONE, AERIAL,

#### STARING

```
Turbulence-mitigation video
processingalgorithms
```

digitalZoom 1, 2, 4

```
Artificial zoom effect by
cropping and inflating pixels
digitally
```

enhancement

#### NONE, CLAHE,

```
LAP, CLAHE9-bit,
CLAHE10-bit
```

```
Improve image quality by
various video processing
algorithms
```

enhancementBlend 0 to 255

```
Blend of fully enhanced
video with unprocessed
video. Higher value = more
enhancement
```

enhancementStrength 0 to 127
Strength of video
enhancement algorithm

focusSpeed 0 to 4 Speed of focus motors

gaussianBlur 0 to 13 Blur strength to the image

```
histogramROIIndex 0 to 7 Region of interest for
histogram calculations
hue 0 to 255 Video hue level
lapMinDiff 0 to 13 LAP adjustment
```

```
noiseFilterMode
```

```
One of
```

- Disabled
- Median3x3
- Gaussian3x3
  Gaussian5x5

```
Noise filter mode
```

```
osdEnabled true or false
```

```
Toggle on-screen text
overlay. Also accessible at
/api/thermal/config/osd
Polarity
```

#### WHITEHOT,

#### BLACKHOT

```
Switches the thermal colors
displayed as hot and cold
```

```
rejectBrightTail 0 to 255
```

```
Reject this precent
(value/10) of the left side of
autogain histogram
```

```
rejectDarkTail 0 to 255
```

```
Reject this precent
(value/10) of the right side
of autogain histogram
sharpen 0 to 1 5
Level of sharpening
algorithm applsied to image
stabilizing true or false
Toggle digital stabilization
feature
statisticsOverlay true or false
Toggle the sensor statistics
overlay on or off
zoomSpeed 0 to 4 Speed of zoom motors
Valid Response Standard
```

## 3.85. Get Thermal Camera Configuration (RS-Series)

```
URL GET /devices/thermal/config
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
```

```
"autofocusMode": "MANUAL",
"colorPalette": "WHITEHOT",
"denoiseMask": "NONE",
"digitalZoom": 4,
"enhancement": "CLAHE",
"focusSpeed": 3,
```

```
"osdEnabled": true,
"polarity": "DEFAULT",
"stabilizing": false,
"targetEnabled": false,
"zoomSpeed": 3,
"imageLevel":
"autogainMinRange": 200,
"autogainUpdateRate": 32,
"brightness": 128,
"contrast": 128,
"denoise": 0,
"enhancementBlend": 200,
"enhancementStrength": 5,
"gain": 0,
"gamma": 13,
"offset": 16,
"sharpen": 0
,
"nuc":
"nucSettingMode": "AUTO",
"nucTable": 1,
"defaultNUCTable": 0
,
"processing":
"enhancement": "MED",
"histogramLevel": "LOW",
"sharpening": "OFF",
"spatialFilter": "LOW",
"temporalFilter": "MED"
}
See Set Thermal Camera Configuration (RS-Series) for information on returned data.
```

## 3.86. Set Thermal Camera Configuration (RS-Series)...................................................................................

```
URL POST /devices/thermal/config
```

```
Comment Sets the thermal camera’s current configuration values. Data structure must
match the example above.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
autofocusMode
MANUAL or
ZOOM_TRIGGER
```

```
Auto focus after zooming, or
only manual control
```

```
colorPalette
```

#### DEFAULT, NONE,

#### WHITEHOT,

#### RAINBOW, IRON,

#### HOTCOLD, JET,

```
Various color palettes
```

#### HOTIRON,

#### IRON256, RAIN256

denoiseMask None, Aerial, Staring Sets the denoise algorithm

digitalZoom 1, 1.5, 2, 4

```
Artificial zoom effect by
cropping and inflating pixels
digitally
```

enhancement

#### NONE, CLAHE,

```
LAP, CLAHE9-bit,
CLAHE10-bit
```

```
Improve image quality by
various video processing
algorithms
```

focusSpeed 3 to 6 Speed of focus motors

osdEnabled true or false

```
Toggle on-screen text
overlay. Also accessible at
/api/thermal/config/osd
```

polarity
DEFAULT or
INVERTED

```
Swap palette temperature
polarity
```

stabilizing true or false
Toggle digital stabilization
feature

targetEnabled true or false Enable crosshairs overlay

zoomSpeed 1 to 6 Speed of zoom motors

**imageLevel**

autogainMinRange 0 to 65535

```
Forces the AGC max/min
spread to be at least this
value
```

autogainUpdateRate 1 to 255
Rate at which AGC max/min
are updated

brightness 0 to 255 Video brightness level

contrast 0 to 255 Video contrast level

denoise 0 to 255

```
Reduce impact of noisy
pixels through video
processing algorithms
```

enhancementBlend 0 to 255

```
Blend of fully enhanced
video with unprocessed
video. Higher value = more
enhancement
```

enhancementStrength 0 to 127
Strength of video
enhancement algorithm

gaussianBlur 0 to 13 Blur strength to the image

lapMinDiff 0 to 13 LAP adjustment

gain -128 to 127 Core processing parameter

gamma -128 to 127 Core processing parameter

offset -128 to 127 Core processing parameter

```
sharpen 0 to 15 Level of sharpening
algorithm applied to image
nuc
```

```
defaultNUCTable 0 to 5
```

```
NUC table the system will
reset to if in
nucSettingMode MANUAL
nucSettingMode AUTO or MANUAL Enable auto-selection
nucTable 0 to 5 Current NUC table
processing
```

```
enhancement
OFF, LOW, MED, or
HIGH Image processing parameter
histogramLevel
```

#### OFF, LOW, MED,

```
HIGH Image processing parameter
sharpening
```

#### OFF, LOW, MED,

```
HIGH Image processing parameter
spatialFilter OFF, LOW, MED,
HIGH
Image processing parameter
```

```
temporalFilter OFF, LOW, MED,
HIGH
Image processing parameter
```

```
Valid Response Standard
```

## 3.87. Get Thermal Camera Configuration (ZS-Series)...................................................................................

```
URL GET /devices/thermal/config
```

```
Comment
```

```
Gets the thermal’s current configuration values.
```

```
zoomSpeed and/or focusSpeed and/or autofocusMode will not be shown if on a
fixed lens system.
Required Data None
Valid Response Ex/
{
"AGLCBrightness": 256,
"AGLCContrast": 128,
"AGLCMode": "AUTO_0",
"DICEEnabled": true,
"DICELevel": 4,
"autofocusMode": "ZOOM_TRIGGER",
"autogainMax": 0,
"autogainMaxExp": 255,
"autogainMin": 0,
"autogainMinExp": 0,
"autogainMinRange": 0,
"autogainMode": "AUTO",
```

```
"autogainROISize": 100,
"autogainUpdateRate": 32,
"automaticShutter": true,
"colorPalette": "WHITE_HOT",
"denoise": 90,
"denoiseMask": "NONE",
"digitalZoom": "1",
"enhancement": "CLAHE",
"enhancementBlend": 200,
"enhancementStrength": 7,
"focusSpeed": 10,
"noiseFilter": true,
"osdEnabled": false,
"sharpen": 0,
"stabilizing": false
}
```

```
See Set Thermal Camera Configuration (ZS-Series) for information on returned data.
```

## 3.88. Set Thermal Camera Configuration (ZS-Series)

```
URL POST /devices/thermal/config
```

```
Comment
```

```
Sets the thermal camera’s current configuration values.
```

```
zoomSpeed and/or focusSpeed and/or autofocusMode are not required if on a
fixed lens system.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
AGLCBrightness 1 to 512
Adjusts the brightness for
manual AGLC mode.
AGLCContrast 1 to 256 Adjusts the contrast for
manual AGLC mode.
AGLCMode AUTO_0, AUTO_1, or
MANUAL
```

```
Automatic Gain Level
Control
DICEEnabled true or false Enable/disable DICE
```

```
DICELevel 1 to 8
Adjusts the intensity of the
DICE processing
autofocusMode MANUAL or
ZOOM_TRIGGER
```

```
Auto focus after zooming, or
only manual control
autogainMax 0 to 65535 Max value of image pixel
data for AGC calculations
autogainMaxExp 0 to 255 Maximum exposure or
integration time
```

autogainMin 0 to 65535 Min value of image pixel
data for AGC calculations

autogainMinExp 0 to 255 Minimum exposure or
integration time

autogainMinRange 0 to 65535

```
Forces the AGC max/min
spread to be at least this
value
```

autogainMode AUTO, MANUAL Mode used to apply
autogain calculations

autogainROISize 25 to 100

```
Region of Interest as
percent of scene for AGC
algorithm
```

autogainUpdateRate 1 to 255 Rate at which AGC max/min
are updated

automaticShutter true or false Also configurable via
/config/autoNUC

colorPalette

#### BLACK_HOT,

#### ICE_FIRE, RAINBOW,

#### SEPID,

```
WARNING_RED or
WHITE_HOT
```

```
Name of active color palette
```

denoise 0 to 255

```
Reduce impact of noisy
pixels through video
processing algorithms
```

denoiseMask None, Aerial, Staring Sets the denoise algorithm

digitalZoom 1, 2, 4, or 8 Digital zoom intensity

enhancement NONE, CLAHE, LAP,
CLAHE9-bit,
CLAHE10-bit

Improve image quality by
various video processing
algorithms
enhancementBlend 0 to 255 Blend of fully enhanced
video with unprocessed
video. Higher value = more
enhancement
enhancementStrength 0 to 127 Strength of video
enhancement algorithm

focusSpeed 10 to 32 Thermal focus speed

noiseFilter true or false Enable noise filter
processing

osdEnabled true or false

```
Toggle on-screen text
overlay. Also accessible at
/api/thermal/config/osd
```

sharpen 0 to 15
Level of sharpening
algorithm applied to image

stabilizing true or false
Toggle digital stabilization
feature

zoomSpeed 10 to 32 Thermal zoom speed

```
Valid Response Standard
```

## 3.89. Get Thermal Camera Automatic NUC Configuration (Z-Series)

```
URL GET /devices/thermal/config/autoNUC
Comment Gets the thermal’s current configuration values.
Required Data None
Valid Response Ex/
{
"enabled": true,
"interval": 10,
"fpaTemperatureThreshold": 0.5,
"ambientTemperatureThreshold": 2.0,
}
```

```
See Set Thermal Camera Automatic NUC Configuration (I-Series) for information on
returned data.
```

## 3.90. Set Thermal Camera Automatic NUC Configuration (Z-Series)...........................................................

```
URL POST /devices/thermal/config/autoNUC
Comment Sets the thermal camera’s current configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
enabled true or false
```

```
interval 1 to 255
```

```
Time in minutes
between NUC
executes
fpaTemperatureThreshold 0.1 to 25 Temperature
difference required to
trigger NUC execution,
in degrees Celsius
```

```
ambientTemperatureThreshold* 0.1 to 25
```

```
Valid Response Standard
```

## 3.91. Get Thermal Camera Encoding Configuration.....................................................................................

```
URL GET /devices/thermal/config/encoding
```

```
Comment Gets the thermal camera’s current encoding configuration values. Not supported
on all series or models
Required Data Ex/
```

#### {

```
"bitrate": 750000,
"bitrateMode": "DEFAULT",
"iframeInteravl": 255
}
See Set Thermal Camera Encoding Configuration f or information on
returned data.
Valid Response Standard
```

## 3.92. Set Thermal Camera Encoding Configuration

```
URL POST /devices/thermal/config/encoding
```

```
Comment Sets the thermal camera’s current encoding configuration values. Not supported
on all series or models
Required Data Format : JSON object
```

```
Parameter Range
bitrate 524288 to 104857600
```

```
bitrateMode DEFAULT, VARIABLE,
CONSTRAINED
iframeInterval 1 to 1024
Valid Response Standard
```

## 3.93. Get Thermal Camera OSD Configuration.............................................................................................

```
URL GET /devices/thermal/config/osd
Comment Gets the thermal camera’s current OSD configuration values.
Required Data Ex/
{
"text": "System 1",
"row": 10,
"column": 10,
"foreground": "GREEN",
"background": "RED",
"enabled": true
}
```

```
Valid Response Standard
```

## 3.94. Set Thermal Camera OSD Configuration

```
URL POST /devices/thermal/config/osd
Comment Sets the thermal camera’s current OSD configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
text Length 0 to 64 OSD displayed text
```

```
row 0 to 512
Vertical location of
OSD text
column 0 to 640
Horizonal location of
OSD text
```

```
foreground
```

#### WHITE, BLACK,

#### GRAY, BLUE,

#### GREEN, RED,

#### TRANSPARENT,

#### AUTOMATIC

```
Color of OSD text
```

```
background
```

#### WHITE, BLACK,

#### GRAY, BLUE,

#### GREEN, RED,

#### TRANSPARENT,

#### AUTOMATIC

```
Color of background
behind OSD text
```

```
enabled true or false
If the text is currently
displayed
Valid Response Standard
```

## 3.95. Get Thermal NUC Table Status (R-Series)............................................................................................

```
URL GET /devices/thermal/status/nuc
```

```
Comment Gets the thermal’s NUC table information. Contact Infiniti for more details about
the returned information.
Required Data None
```

**Valid Response Format** : List of JSON objects

```
Parameter Description
active If this NUC table iscurrently active
focusPosition Focus range this table is active in
fovIndex FOV range this table is active in
index Table index
integrationTime Integration time value for NUC calculations
t1
t2
t3
tableSize Table size in memory
zoomPosition Zoom range this table is active in
```

**Valid Response** _Ex/_

```
[
{
"integrationTime": 14900,
"t3": 11,
"t2": 18,
"tableSize": 327680,
"focusPosition": 13643,
"zoomPosition": 12548,
"t1": 5,
"index": 14,
"fovIndex": 4,
"active": false
},
```

#### {

```
"integrationTime": 10400,
"t3": 21,
"t2": 28,
"tableSize": 327680,
"focusPosition": 12763,
"zoomPosition": 46,
"t1": 15,
"index": 15,
"fovIndex": 0,
```

```
"active": true
}
]
```

## 3.96. Get Thermal Cooler Status (V-Series)..................................................................................................

```
URL GET /devices/thermal/cooler/status
```

```
Comment Gets the thermal’s cooler status and cycle history. Contact Infiniti for more details
about the returned information.
Required Data None
Valid Response Ex/
{
"totalRunTime": 14568,
"coolerCycles": 16,
"referenceCooldownRecord": {
"cooldownTotalTime": 100,
"cooldown223KTime": 100,
"cycleStartTemp": 10,
"cycleFinalTemp": 10
"longCooldownRecord": {
"cooldownTotalTime": 100,
"cooldown223KTime": 100,
"cycleStartTemp": 10,
"cycleFinalTemp": 10
},
"previousCooldownRecord": {
"cooldownTotalTime": 100,
"cooldown223KTime": 100,
"cycleStartTemp": 10,
"cycleFinalTemp": 10
},
"currentCooldownRecord": {
"cooldownTotalTime": 100,
"cooldown223KTime": 100,
"cycleStartTemp": 10,
"cycleFinalTemp": 10
},
}
```

## 3.97. Get Thermal Camera Status (Z-Series)

```
URL GET /devices/thermal/status
```

```
Comment Gets the thermal’s current status. These are either non-configurable values, or
values that are set through dedicated endpoints.
```

```
Required Data None
Valid Response Ex/
{
"fpaTemperature": 24.73,
"cameraTemperature": 26.5
}
Both temperatures are given in degrees Celsius
```

## 3.98. Perform Internal 1-Point NUC

```
URL GET /devices/thermal?command=1NUCInternal
```

```
Comment Performs an internal 1-point NUC. Note that the effects of this process may be
reverted when switching between NUC indexes.
Required Data None
Valid Response Standard
```

## 3.99. Perform External 1-Point NUC.............................................................................................................

```
URL GET /devices/thermal?command=1NUCExternal
```

```
Comment Performs an external 1-point NUC. Note that the effects of this process may be
reverted when switching between NUC indexes.
Required Data None
Valid Response Standard
```

## 3.100. Perform Optical 1-Point NUC...............................................................................................................

```
URL GET /devices/thermal?command=1NUCOptical
```

```
Comment Performs an optical 1-point NUC. Note that the effects of this process may be
reverted when switching between NUC indexes.
Required Data None
Valid Response Standard
```

## 3.101. Get OSD Menu Status..........................................................................................................................

```
URL GET /devices/thermal/OSDMenu
```

```
Comment Gets the current status of the OSD Menu if present on the thermal system, either
active or not.
Required Data None
```

```
Valid Response
Ex/
{
```

```
"open": true
}
```

## 3.102. Open OSD Menu..................................................................................................................................

```
URL GET /devices/thermal?command=openOSDMenu
Comment Activates the OSD Menu
Required Data None
Valid Response Standard
```

## 3.103. Close OSD Menu..................................................................................................................................

```
URL GET /devices/thermal?command=closeOSDMenu
```

```
Comment Deactivates the OSD Menu. Ensure all changes are saved before exiting. Note
that this command is only relevant if the OSD Menu is currently active.
Required Data None
Valid Response Standard
```

## 3.104. Navigate OSD Menu

```
URL GET /devices/thermal?command=navigateOSDMenu&
direction=<DIRECTION>
```

```
Comment
```

```
Note that this command is only relevant if the OSD Menu is currently active.
```

```
Direction can be one of up , down , left , right. Typically, up and down are used to
navigate between menu items, and left and right are used to select an option or
change the value of a selection.
Required Data The DIRECTION string describing which direction to move the OSD menu cursor
Valid Response Standard
```

## 3.105. Get LRF Status......................................................................................................................................

```
URL GET /devices/lrf/status
```

```
Comment Gets the lrf’s status. These are either non-configurable values, or values that are
set through dedicated endpoints.
Required Data None
Valid Response Ex/
{
"lowVoltageThreshold": 991,
"measuredRate": 235,
```

```
"pulseWidths": [
13235,
5569,
etc...
]
}
```

```
Note that pulseWidths field will only be populated after at least one range
request has been sent
```

## 3.106. Get LRF Configuration..........................................................................................................................

```
URL GET /devices/lrf/config
Comment Gets the configuration information of the LRF.
Required Data None
Valid Response Ex/
{
"highRepetitionRateMode": false,
"highVoltageThreshold": 1331,
"maxReportedRange": 250000,
"multiPulseBinAdjacency": 5,
"multiPulseLaserShots": 7,
"multiPulseThreshold": 2,
"receiverGainMode": 0,
"reportedRangeReturns": 7
}
```

```
See Set LRF Configuration for information on returned data.
```

## 3.107. Set LRF Configuration

```
URL POST /devices/lrf/config
Comment Sets the configuration of the LRF.
Required Data Format : JSON object
```

```
Parameter Range Description
highRepetitionRateMode true or false When enabled, prevents the
device from going into
standby mode, increasing
power usage but improving
response time.
highVoltageThreshold 0 to 4095 The max voltage threshold
measured in millivolts (mV)
```

```
maxReportedRange 0 to 640,000 The furthest range that may
be reported
multiPulseBinAdjacency 1 to 5 Related to the
multiPulseThreshold
parameter, this defines the
difference in range required
before ranges are merged
into one return.
multiPulseLaserShots 2 to 10 Specifies thenumber of times
a laser fires for a multi-pulse
command.
multiPulseThreshold 2 to 10 The number of coincident
range returns that can be
combined into one range
result
receiverGainMode 0 to 3 Sets the gain mode of the
photoreceiver.
```

```
0 : Maximum damage
threshold
1 : Optimum for 60 Hz false
alarm rate (FAR)
2 : Unused
3 : Optimum for 15 kHz FAR
reportedRangeReturns 1 to 20 Sets the max numberof
returns from a single-pulse
command.
Valid Response Standard
```

## 3.108. Reset LRF Configuration

```
URL GET /devices/lrf?command=resetConfig
Comment Resets the configuration values of the LRF to factory defaults.
Required Data None
Valid Response Standard
```

## 3.109. LRF Range Request

```
URL GET /devices/lrf?command=<RANGE COMMAND>
Comment Sends either a single-pulse (SPR) or multi-pulse (MPR) range request, which can
be auto-calibrated to increase accuracy but may take longer to execute.
```

```
Command Description
```

```
SPR Single-pulse range request
MPR Multi-pulse range request
```

```
autoSPR
Auto-calibrated single-pulse
request
autoMPR
```

```
Auto-calibrated multi-pulse
request
slowMPR
```

```
Continuous1Hz multi-pulse
range request
medMPR
```

```
Continuous 4Hz multi-pulse
range request
```

```
fastMPR
```

```
Continuous 10Hz multi-pulse
range request
```

```
stopContinuous
```

```
Stop continuous multi pulse
range request
Required Data The type of range command to be used
Valid Response Ex/
{
"ranges": [54.2, 1320.5, 3733.2]
}
```

```
Units for range results are always reported in meters
```

## 3.110. Get LRF Range Request Report............................................................................................................

```
URL GET /devices/lrf?command=report<METRIC>
Comment Sends a range request and processes the data to provide specific information
about the request.
```

```
The METRIC parameter can be any of the following keywords:
```

```
Metric / Command Description
First The first range returned
Last The last range returned
```

```
Longest The longest range returned
Strongest The range with the widest pulse width
Mean The average of the returned ranges
```

```
WeightedMean
```

```
The average of the returned ranges, weighted by
pulse widths
All
Gather all metrics, including ranges and pulse
widths
```

```
Ex/
```

```
/devices/lrf?command=reportAll
Required Data None
Valid Response Ex/
{
"firstRange": 54.0,
"lastRange": 3733.2,
"strongestRange": 1320.5,
"longestRange": 3733.2,
"meanRange": 1702.57,
"weightedMeanRange": 2156.29,
"ranges": [54.0, 1320.5, 3733.2],
"pulseWidths": [38572, 2038, 17950, 12231]
}
```

```
The above response was returned from a reportAll command.
```

## 3.111. Calibrate LRF for False Alarm Rate

```
URL GET /devices/lrf?command=calibrate[&rate=<RATE>]
Comment Calibrates the LRF for the given false alarm rate of the device (or a default rate if
none is given), which can improve the accuracy of range results. This command is
automatically performed during the autoSPR and autoMPR commands.
```

```
An optional RATE parameter can be given, which can range from 0 to
1,000,000,000 Hz (1 GHz). If no rate is given, the false alarm rate will be
calibrated to 120-300 Hz.
Required Data None
Valid Response {
"falseAlarmRateSet": true,
"currentLowVoltageThreshold": 1011,
"previousLowVoltageThreshold": 991
}
```

```
The falseAlarmRateSet field indicates whether the false alarm rate has been
changed through calibration. The effect of the calibration can be seen by
comparing the currentLowVoltageThreshold and previousLowVoltageThreshold
values. If the current threshold is lower than the previous, the noise floor has
been lowered to allow more results. If the current threshold is higher than the
previous, the noise floor has been raised to reduce potential false results.
```

## 3.112. Get LRF AHRS Sample..........................................................................................................................

```
URL GET /devices/lrf/ahrs
Comment Gets a sample of the LRF's AHRS reading.
Required Data None
Valid Response Ex/
{
"heading": 159.01,
"ahrsStatus": 16,
"roll": 2.95,
"pitch": -23.39
}
```

```
The ahrsStatus parameter is defined by the following bit field:
```

```
0-2 : Reserved
3 : Calibration status. A status of 1 indicates AHRS calibration is complete.
4 : Magnetic transient detection
5 : Unreliable sensor data
```

```
If you suspect that the AHRS in your system is not producing accurate results,
retrieve this status field and contact Infiniti for support.
```

## 3.113. Get LRF AHRS Configuration................................................................................................................

```
URL GET /devices/lrf/ahrs/config
Comment Gets the configuration for the LRF's AHRS.
Required Data None
```

```
Valid Response
```

```
Ex/
```

```
{
"declination": 0,
"headingOffset": 0,
"rollOffset": 0,
"pitchOffset": 0
}
```

## 3.114. Set LRF AHRS Configuration.................................................................................................................

```
URL POST /devices/lrf/ahrs/config
```

```
Comment Sets the configuration for the LRF's AHRS. This command is useful when defining
a home position or base reference point for orientation.
```

```
Required Data Format : JSON object
```

```
Parameter Range
declination -1000 to 1000 exclusive
headingOffset -1000 to 1000 exclusive
```

```
rollOffset -1000 to 1000 exclusive
pitchOffset -100 to 100 exclusive
Valid Response Standard
```

## 3.115. Initialize LRF AHRS

```
URL GET /devices/lrf/ahrs?command=initialize
Comment Initializes the LRF’s AHRS. This must be done before requesting an AHRS sample.
Note that even while the AHRS is not initialized, it may still return the values of
the latest sample. In this case, please initialize to receive up-to-date positioning
data.
Required Data None
Valid Response Standard
```

## 3.116. De-initialize LRF AHRS..........................................................................................................................

```
URL GET /devices/lrf/ahrs?command=deinitialize
Comment De-initializes the LRF’s AHRS. This can be done to reduce power usage.
Required Data None
Valid Response Standard
```

## 3.117. Get ZLID Status

```
URL GET /devices/zlid/status
Comment Gets the current state of the ZLID.
Required Data None
Valid Response Ex/
{
"mode": "auto"
"laserActive": true
}
```

```
mode ─ The current operational mode of the laser, which can be one of auto or
off
```

```
laserActive ─ The state of the laser diode. Note that even though this value may
immediately change to true once the system detects that the photocell is reading
daytime values, the laser diode itself may take up to 30 seconds to activate.
```

## 3.118. Get ZLID Intensity

```
URL GET /devices/zlid/intensity
Comment Gets the current laser diode intensity percentage. This can be used to reduce the
power for eye-safety concerns or for viewing targets to close that appear over-
saturated with light. Please use with caution; refer to the laser safety warnings
and training guide before attempting any operations.
Required Data None
Valid Response Ex/
{
"intensity": 90
}
```

## 3.119. Set ZLID Intensity.................................................................................................................................

```
URL GET /devices/zlid/intensity
Comment Sets the laser diode intensity. Values below 100% will produce weaker beam
strength than the full capacity. This can be used to reduce the power for eye-
safety concerns or for viewing targets to close that appear over-saturated with
light. USE WITH CAUTION ; refer to the laser safety warnings and training guide
before attempting any operations.
```

```
Required Data
```

```
Format : JSON object
```

```
Parameter Range
intensity 0 to 100
```

```
Valid Response Standard
```

## 3.120. Get ZLID Position

```
URL GET /devices/zlid/position
Comment Gets the current magnification percentage of the laser. Lower zoom values
indicate a wider and less concentrated beam, and higher values indicate a
narrower, more concentrated one. Higher zoom levels are better for longer
distances.
Required Data None
```

```
Valid Response Ex/
{
"zoom": 57.042
}
```

## 3.121. Set ZLID Position..................................................................................................................................

```
URL POST /devices/zlid/position
Comment Sets the current magnification percentage of the laser.
Required Data Format : JSON object
```

```
Parameter Range
zoom 0 to 100
Valid Response Standard
```

## 3.122. Start ZLID Motor..................................................................................................................................

```
URL GET /devices/zlid?command=<MOVE COMMAND>
Comment Adjusts the ZLID's magnification level by moving the collimator motor in a given
direction. MOVE COMMAND can be one of the following values:
```

```
Command Description
zoomWide Increase laserbeam width
zoomTele Decreaselaser beam width
Required Data The lens movement command to be used
Valid Response Standard
```

## 3.123. Stop ZLID Motor...................................................................................................................................

```
URL GET /devices/zlid?command=stop
Comment Stops ZLID collimator movement.
Required Data None
Valid Response Standard
```

## 3.124. Change ZLID Laser Mode

```
URL GET /devices/zlid?command=<on OR off>
```

```
Comment
```

```
Turns on or off the ZLID. If the ZLID is within a system that has an activated
photocell, then the on command will place the laser diode in an AUTO state, that
will be activated when the photocell reads darkness, and deactivated when the
photocell reads enough light. If there is no photocell present, then the on
command will activate the diode directly and must be used with EXTREME
CAUTION for systems with an NOHD value. Please consult Infiniti directly if you
have any questions or safety concerns regarding the safe operation of our ZLID
systems.
```

```
In all situations, the off command will prevent the diode from emitting any light,
but the ZLID will retain its ability to collimate and communicate.
```

```
For more information about ZLID operation and laser safety, please refer to the
ZLID Operational and Safety Training Guide. ALL OPERATORS MUST BE TRAINED
in safe usage of ZLID-enabled systems before system control is handed over.
Required Data The ZLID mode
Valid Response Standard
```

## 3.125. Get Search Light Configuration............................................................................................................

```
URL GET /devices/searchLight/config
Comment Gets the search Light’s configuration.
Required Data None
Valid Response Ex/
{
"intensity": "OFF",
"strobe": "OFF"
}
```

## 3.126. Set Search Light Configuration

```
URL POST /devices/searchLight/config
Comment Sets the search Light’s configuration.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
intensity
```

#### LOW, NORMAL,

```
HIGH or OFF Intensity
strobe ON or OFF Strobe
Valid Response Standard
```

## 3.127. Get Encoder Ethernet Configuration...................................................................................................

```
URL GET /devices/encoder/config/ethernet
Comment Gets the encoder’s ethernet configuration information.
Required Data None
Valid Response Ex/
{
"host": "192.168.0.140",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1",
"port": 80,
"username": "admin",
"password": "admin"
}
```

## 3.128. Set Encoder Ethernet Configuration....................................................................................................

```
URL POST /devices/encoder/config/ethernet
Comment Sets the encoder’s ethernet configuration information.
Required Data IPv4 network configuration data matching the format in the example above. Note
that by default the username and password may use a reserved ‘Octagon’
account on the corresponding device and should not be changed without first
consulting an Infiniti technician.
```

```
Valid Response Standard
```

## 3.129. Get GPS Status.....................................................................................................................................

```
URL GET /devices/gps/status
```

```
Comment Get all available information from the GPS device. Real-time and spatial accuracy
are dependent on model.
Required Data None
```

```
Valid Response
```

```
* - Not included on all models
```

```
Parameter Description
uptime Time since startup in format " hhmmss.ss "
latitude Current position
latitudeDirection 'N' or 'S'
longitude Current position
```

```
longitudeDirection 'W' or 'E'
```

```
quality* One of Fix Not Available , GPS Fix , or
Differential GPS Fix
satelliteCount* Number of satellites in view, 00 - 12
horizontalDilution* Horizontal Dilution of precision
```

```
altitude* Antenna altitude above/below mean-sea-level
(geoid). Given in meters
```

```
geoidalSeparation*
```

```
Geoidal separation, the difference between the
WGS-84 earth ellipsoid and mean-sea-level
(geoid). Given in meters
ageOfDifferential* Age of differential GPS data
differentialReferenceStation Differential reference station ID, 0000-1023
```

## 3.130. Get GPS Position..................................................................................................................................

```
URL GET /devices/gps/position
```

```
Comment Get key data from the GPS device. Real-time and spatial accuracy are dependent
on model.
Required Data None
```

```
Valid Response
```

```
Ex/
{
"latitude": "49.5022291 N",
"longitude": "115.7657758 W",
"altitude": 973.4
}
```

```
The altitude value is given in meters
```

## 3.131. Get SWIR Status...................................................................................................................................

```
URL GET /devices/swir/status
```

```
Comment
```

```
Gets the SWIR camera’s status. These are either non-configurable values or
values that are set through dedicated endpoints. Temperatures are returned in
degrees Celsius.
Required Data None
Valid Response Ex/
{
"lensTemperature": 28.47,
"sensorTemperature": 34.01,
"fpaTemperature": 17.98,
"lensErrors": null,
```

```
"tecStatus": LOCKED,
"tecSetpoint": 18.0,
"oprCount": 48
}
```

## 3.132. Get SWIR Lens Position........................................................................................................................

```
URL GET /devices/swir/position
Comment Gets the zoom and focus positions of the SWIR lens in percentage.
Required Data None
Valid Response Ex/
{
"zoom": 53.50,
"focus": 48.81
}
```

## 3.133. Set SWIR Lens Position

```
URL POST /devices/swir/position
Comment Set the zoom and focus positions of the SWIR lens in percent.
Required Data Format : JSON object
```

```
Parameter Range
zoom 0 to 100
focus 0 to 100
Valid Response Standard
```

## 3.134. Get SWIR Configuration.......................................................................................................................

```
URL GET /devices/swir/config
Comment Gets the SWIR’s current configuration values.
Required Data None
Valid Response Ex/
{
"BCInq": "OFF",
"DPCDatasetCount": 1,
"DPCMode": "ON",
"adjustTolAutoExposure": "5.0 %",
"agcEnabled": true,
```

"autoContrastMode": "OFF",
"autoExposureRate": "100.0 %",
"autoexposureMode": "OFF",
"autofocusMode": "MANUAL",
"brightness": 128,
"contrast": 128,
"denoise": 0,
"denoiseMask": "OFF",
"detectorEnhancementAuto": false,
"detectorEnhancementEnabled": true,
"detectorEnhancementFrameAverage": 0,
"detectorEnhancementPower": 0.6,
"enhancement": "CLAHE",
"enhancementBlend": 255,
"enhancementStrength": 5,
"exposureTime": 5.0,
"focusSpeed": 7,
"gain": "Gain0",
"gaussianBlur": 0,
"hue": 0,
"lapMinDiff": 0,
"maxExposureValue": 29826.161,
"minAutoExposure": 0.006,
"minExposureValue": 0.001,
"nucActiveDataset": 1,
"nucAutoDatasetMode": "CONTINUOUS",
"nucDatasetActiveDescription": "Gain",
"nucDatasetActiveExposureTime": 5.0,
"nucDatasetActiveGain": "Gain0",
"nucDatasetActiveTemperature": "45.00°C",
"nucDatasetCount": 19,
"nucDatasetDescription": "Gain",
"nucDatasetNodeCount": 2,
"nucDatasetNodeSelector": 0,
"nucDatasetSelector": 0,
"nucInq": "ON",
"nucMode": "TwoPoint",
"operatingMode": "DEFAULT",
"oprCurrent": 12,
"osdEnabled": false,
"serialPortBaudRate": "Baud19200",
"sharpen": 5,
"stabilizing": true,
"tecEnabled": true,
"userCount": 5,
"userSetDefault": "Default",
"userSetInq": "UserSetNotSupported",

```
"userSetNum": "Default"
"zoomSpeed": 1
}
See Set SWIR Configuration for information on returned data.
```

## 3.135. Set SWIR Configuration

```
URL POST /devices/swir/config
Comment Sets the SWIR’s current configuration values.
Required
Data
```

```
Format : JSON object
```

```
Parameter Range Description
```

```
BCInq OFF or ON Background Correction
Mode
DPCMode OFF or ON Defect Pixel Correction
Mode
```

```
adjustTolAutoExposure 0 – 100(percent%)
```

```
Tolerance, for specific
target value within which
auto exposure does not
run.
```

```
agcEnabled true or false
```

```
Toggle using frame
statistics to automatically
select the appropriate
OPR index
```

```
autoContrastMode
```

```
OFF, WholeImage
or
AutoModeRegion
```

```
Automatic contrast mode
```

```
autoExposureRate 0 – 100(percent%)
```

```
Rate of exposure
adjustment, to slow down
the auto-exposure
adjustments.
```

```
autoexposureMode
```

#### OFF,

```
CONTINUOUS or
ONCE
```

```
Automatic exposure mode
```

```
autofocusMode MANUAL or
ZOOM_TRIGGER
```

```
Auto focus after zooming,
or only manual control
brightness 0 to 255 Video brightness level
contrast 0 to 255 Video contrast level
```

```
denoise 0 to 255
```

```
Reduce impact of noisy
pixels through video
processing algorithms
```

denoiseMask NONE, AERIAL,
STARING

```
Turbulence-mitigation
video processing
algorithms
```

detectorEnhancementAuto true or false

```
When enabled, uses
internal algorithm to set
other enhancement
settings automatically
from scene information
```

detectorEnhancementEnabled true or false Enable/disable the
enhancement algorithm

detectorEnhancementFrameAverage 0 to 5 (INTEGER)

```
Sets the number of
frames over which
enhancement frame
statistics are calculated
```

detectorEnhancementPower 0 to 10

```
Sets the aggressiveness of
the enhancement
algorithm
```

enhancement

#### NONE, CLAHE,

```
LAP, CLAHE9-bit,
CLAHE10-bit
```

```
Improve image quality by
various video processing
algorithms
```

enhancementBlend 0 to 255

```
Blend of fully enhanced
video with unprocessed
video. Higher value =
more enhancement
```

enhancementStrength 0 to 127 Strength of video
enhancement algorithm

executeUserSet Load or Save

```
Loads or save camera
parameters from the user
set (Default settings
cannot be overwritten)
```

exposureTime

```
minExposureLimit-
maxExposureLimit
(milli-Second)
```

```
Exposure duration
currently set
```

focusSpeed 0 to 7 Speed of focus motors

gain Gain0, Gain1 or
Gain2
FPA gain level

gaussianBlur 0 to 13 Blur strength to the image

lapMinDiff 0 to 13 LAP adjustment

minAutoExposure

```
minExposureLimit-
maxExposureLimit
(milli-Second)
```

```
Minimum auto exposure
value
```

nucAutoDatasetMode OFF, ONCE or
CONTINUOUS

```
Controls automatic
selection of nuc dataset
active
```

```
nucDatasetNodeSelector^0 – camera
dependent
```

```
Selects datapoint of
dataset for accessing
dataset properties.
nucDatasetSelector^0 – camera
dependent
Selects dataset for access
```

```
nucMode OFF or TwoPoint Controls operation mode
of NUC
```

```
operatingMode
```

#### DEFAULT,

```
HIGH_TEMP, or
EXTREME_HEAT
```

```
Pre-configured operating
modes that affect a
variety of settings
oprCurrent 0 to 48 Currently activated
operational setting index
```

```
osdEnabled true or false
```

```
Toggle on-screen text
overlay. Also accessible at
/api/swir/config/osd
```

```
serialPortBaudRate
```

```
Baud9600,
Baud19200,
Baud38400,
Baud57600,
Baud115200,
Baud230400,
Baud460800 or
Baud921600
```

```
Controls data
transmission rate used by
selected serial port.
```

```
sharpen 0 to 15
```

```
Level of sharpening
algorithm applied to
image
stabilizing true or false Toggle digital stabilization
feature
tecEnabled true or false Enable/disables the TEC
(thermoelectric cooler)
```

```
userSetDefault
```

```
Default,
UserSet1,
UserSet2,
UserSet3,
UserSet4,
UserSet5
```

```
Selects user-set that to be
loaded on power-up or
reset
```

```
userSetNum
```

```
Default,
UserSet1,
UserSet2,
UserSet3,
UserSet4,
UserSet5
```

```
Selects user-set for
loading or saving camera
parameter
```

```
zoomSpeed 0 to 7 Speed of zoom motors
```

**Valid
Response** Standard

## 3.136. Get SWIR Camera Encoding Configuration..........................................................................................

```
URL GET /devices/swir/config/encoding
```

```
Comment Gets the SWIR camera’s current encoding configuration values. Not supported on
all series or models
Required Data Ex/
{
"bitrate": 750000,
"bitrateMode": "DEFAULT",
"iframeInteravl": 255
}
See Set SWIR Camera Encoding Configuration f or information on
returned data.
Valid Response Standard
```

## 3.137. Set SWIR Camera Encoding Configuration

```
URL POST /devices/swir/config/encoding
```

```
Comment
Sets the SWIR camera’s current encoding configuration values. Not supported on
all series or models
Required Data Format : JSON object
```

```
Parameter Range
bitrate 524288 to 104857600
```

```
bitrateMode
```

#### DEFAULT, VARIABLE,

#### CONSTRAINED

```
iframeInterval 1 to 1024
Valid Response Standard
```

## 3.138. Get SWIR Camera Ethernet Configuration

```
URL GET /devices/swir/config/ethernet
Comment Gets the SWIR camera’s ethernet configuration information.
Required Data None
Valid Response Ex/
{
"host": "192.168.0.179",
"subnet": "255.255.252.0",
"gateway": "192.168.0.1".
"recvPort": 14002,
```

```
"sendPort": 14001,
"octagonAddress": "192.168.0.239"
```

```
}
```

## 3.139. Set SWIR Camera Ethernet Configuration...........................................................................................

```
URL POST /devices/swir/config/ethernet
Comment Sets the SWIR camera’s ethernet configuration information.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
host IPv4 valid address
Address of the thermal
system
subnet
IPv4 valid subnet
mask
Subnet Mask
```

```
gateway IPv4 valid address
Address of gateway
router
```

```
recvPort 1 to 65535
```

```
Port that the Octagon
system will receive data
from the thermal device
```

```
sendPort 1 to 65535
```

```
Port that the Octagon
system will send data to
the thermal device
```

```
octagonAddress IPv4 valid address
```

```
This address can either
be set to the
configurable octagon
address or the secondary
static 60.61.62.60
Valid Response Standard
```

## 3.140. Get SWIR Camera OSD Configuration

```
URL GET /devices/swir/config/osd
Comment Gets the SWIR camera’s current OSD configuration values.
Required Data Ex/
{
"text": "System 1",
"row": 10,
"column": 10,
"foreground": "GREEN",
```

```
"background": "RED",
"enabled": true
}
```

```
Valid Response Standard
```

## 3.141. Set SWIR Camera OSD Configuration

```
URL POST /devices/swir/config/osd
Comment Sets the SWIR camera’s current OSD configuration values.
Required Data Format : JSON object
```

```
Parameter Range Description
text Length 0 to 64 OSD displayed text
```

```
row 0 to 512 Vertical location of
OSD text
column 0 to 640 Horizonal location of
OSD text
```

```
foreground
```

#### WHITE, BLACK,

#### GRAY, BLUE,

#### GREEN, RED,

#### TRANSPARENT,

#### AUTOMATIC

```
Color of OSD text
```

```
background
```

#### WHITE, BLACK,

#### GRAY, BLUE,

#### GREEN, RED,

#### TRANSPARENT,

#### AUTOMATIC

```
Color of background
behind OSD text
```

```
enabled true or false If the text is currently
displayed
Valid Response Standard
```

## 3.142. Select SWIR User set............................................................................................................................

```
URL GET /devices/swir?command=selectUserSet&mode=<UserMode>
```

```
Comment
```

```
Selects User set from user set mode, for loading or saving camera parameters.
mode Description
Default System Default mode
```

```
UserSet1 User Set Mode 1
UserSet2 User Set Mode 2
```

```
UserSet3 User Set Mode 3
UserSet4 User Set Mode 4
UserSet5 User Set Mode 5
Required Data None
Valid Response Ex/
{
"success": true,
"data": null
}
```

## 3.143. Save SWIR User set..............................................................................................................................

```
URL GET /devices/swir?command= saveUserSet
Comment Save camera parameters to selected user set.
Required Data None
Valid Response Ex/
{
"success": true,
"data": null
}
```

## 3.144. Get Active NUC dataset.......................................................................................................................

```
URL GET /devices/swir?command= getActiveNUCDataset
Comment Get the active nuc datasets.
Required Data None
Valid Response Ex/
{
"success": true,
"data": null
}
```

## 3.145. Set Active NUC dataset........................................................................................................................

```
URL GET /devices/swir?command= setActiveNUCDataset&dataset=<dataset>
```

```
Comment Set the active nuc datasets.
dataset=<0 - device_dependent>
Required Data None
```

```
Valid Response Ex/
{
"success": true,
"data": null
}
```

## 3.146. Move SWIR Lens..................................................................................................................................

```
URL GET /devices/swir?command=<MOVE COMMAND>
Comment Moves the SWIR lens’ zoom or focus motors in the specified direction.
```

```
Command Description
zoomTele Startsthe zoom motor in the tele direction.
zoomWide Starts thezoom motor in the wide direction.
focusFar Starts the focus motor in the far direction.
focusNear Starts thefocus motor in the near direction.
Ex/
```

```
/devices/swir?command=zoomTele
```

```
Required Data The COMMAND string
Valid Response Standard
```

## 3.147. Start SWIR Auto-Focus.........................................................................................................................

```
URL GET /devices/swir?command=autofocus
Comment Executes an auto-focus sequence with the SWIR lens.
Required Data None
Valid Response Standard
```

## 3.148. Stop SWIR Lens....................................................................................................................................

```
URL GET /devices/swir?command=stop
Comment Stops both zoom and focus motors of the SWIR lens.
Required Data None
Valid Response Standard
```

## 3.149. Initialize SWIR Camera.........................................................................................................................

```
URL GET /devices/swir?command=initializeCamera
Comment Initializes SWIR camera
Required Data None
Valid Response Standard
```

## 3.150. Set SWIR Camera Digital Stabilization.................................................................................................

```
URL GET /devices/swir?command=stabilization&enable=<true OR false>
Comment Activate or deactivate the digital stabilization function on the SWIR camera
Required Data A value of true or false to enable or disable stabilization
Valid Response Standard
```

## 3.151. Set SWIR Autofocus Mode...................................................................................................................

#### URL

```
GET /devices/swir?command=zoomTriggerAutofocus&enable=<true OR
false>
```

```
Comment
```

```
Sets the lens’ autofocus mode. If enabled, the lens will perform an autofocus
whenever zooming has stopped. When inactive, the autofocus command must be
called manually.
Required Data Either true or false to enable or disable zoom-trigger autofocus.
Valid Response Standard
```

## 3.152. Get Modules

```
URL GET /modules
Comment Gets the information for all modules.
Required Data None
Valid Response Ex/
{
"pelcoSystemController": {
"lastConfigUpdate": "2007-11-06T16:34:41.000Z",
"status": "ACTIVE"
},
"laserSync": {...},
"gps": {...},
...
}
```

```
lastConfigUpdate ─ The last time the configuration for this module was updated
```

```
The status parameter can be one of the following values:
```

```
Status Description
INACTIVE The module has been deactivated
```

```
INVALID The validation process failed for this
module
ACTIVE The module is operating normally
```

#### ERROR

```
The module has encountered an
error, whose error object is
returned in the lastError field
```

## 3.153. Get Module State

```
URL GET /modules/<MODULE>
Comment Gets the information for the given MODULE.
Required Data The module name
Valid Response Ex/
{
"lastConfigUpdate": "2007-11-06T16:34:41.000Z",
"status": "ACTIVE"
}
```

```
See Get Modules for information on returned data.
```

## 3.154. Activate / Deactivate Module..............................................................................................................

```
URL GET /modules/<MODULE>?activate=<true OR false>
```

```
Comment
```

```
Activates or deactivates the given module. Update the initiallyActive value found
in the /modules/<MODULE>/config to have activation persist through system
restarts.
Required Data The module name, plus a boolean value indicating whether to activate (true) or
deactivate (false) the module.
Valid Response Standard
```

## 3.155. Get Auto Tracking Status.....................................................................................................................

```
URL GET /modules/autoTracking/status
```

```
Comment Gets the status of auto tracking.
```

```
Parameter Description
```

```
autotrackingFps FPS of auto tracking movement. See
/config framePeriod for more details.
currentState Is auto track currently following a tracked
object
lastPantiltMovement Time of last pantilt movement
lastTelemetryMessage Time of last track telemetry received
version Current auto tracking module version
Required Data None
Valid Response Ex/
{
"autotrackingFps": 15.0,
"currentState": "FOLLOWING",
"lastPantiltMovement": "2021-05-26T18:09:07.718664",
"lastTelemetryMessage": "2021-05-26T18:13:41.870830",
"trackIndex": 1,
"version": 0.04.000000
}
```

## 3.156. Get Auto Tracking Configuration.......................................................................................................

```
URL GET /modules/autoTracking/config
```

```
Comment Gets auto tracking basic configuration values.
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"autoStartTrack": "DRONE",
"cancelStuckTracks": true,
"centerStop": true,
"currentDevice": "visible",
"devicePictureInPicture": "VISIBLE",
"framePeriod": 2,
"homePosition": {
"pan": null,
"tilt": null,
"zoom": null
},
"serverPort": 8009,
"zoomOutIncrement": 3
```

#### }

```
See Set Auto Tracking Configuration for information on returned data.
```

## 3.157. Set Auto Tracking Configuration........................................................................................................

```
URL POST /modules/autoTracking/config
```

```
Comment
```

```
Sets auto tracking basic configuration values. See Introduction > Optional
Features for more details.
```

```
Persists on system restarts.
```

```
Required Data Format : JSON object
```

```
Parameter Range Description
initiallyActive true or false Module starts on power up
```

```
autoStartTrack
```

#### NONE, ALL, DRONE,

#### VEHICLE, STICKY

```
On target detection,
automatically tracks highest
confidence object, filtered
by classification.
```

```
cancelStuckTracks true or false
```

```
Cancels tracked objects
labelled as BACKGROUND
after 4 seconds
```

```
centerStop true or false
```

```
If object is centered, it will
stop pantilt movement
```

```
currentDevice VISIBLE, THERMAL
```

```
Camera device auto
tracking is currently running
on
```

```
devicePictureInPicture OFF, VISIBLE
```

```
Add zoomed in picture-in-
picture of detected objects
to screen
```

```
framePeriod 1 to 60
```

```
The refresh rate of auto
tracking PTZ control. Frame
period is dependent on
video processing FPS. See
/status for real auto
tracking FPS. Value of 1-3 is
recommended.
```

```
serverPort 0 to 65535
```

```
System telemetry receive
port
```

```
zoomOutIncrement 0 to 10
```

```
If value > 0, camera will
zoom out by this value
percent if tracked object is
at edge of screen
```

```
homePosition
```

```
pan null or float
```

```
Reset pan to position if
track is lost
```

```
tilt null or float
```

```
Reset tilt to position if track
is lost
```

```
zoom null or float
```

```
Reset zoom to position if
track is lost
Valid Response Standard
```

## 3.158. Get Auto Tracking Advanced Configuration......................................................................................

```
URL GET /modules/autoTracking/config/advanced/<DEVICE>
```

```
Comment
```

```
Gets <DEVICE> advanced tracking and detection configuration values.
```

```
<DEVICE> The name of the camera device
Required Data None
Valid Response Ex/
{
"detectionMode": "DRONE CLASSIFIED",
"enableAcquisitionAssist": true,
"enableIntelligentAssist": true,
"highNoiseCompensation": false,
"maxFrameMiss": 120,
"nearValue": 500,
"objectSize": 40,
"sensitivity": 5
}
See Set Auto Tracking Advanced Config for information on returned data.
```

## 3.159. Set Auto Tracking Advanced Configuration.......................................................................................

```
URL POST /modules/autoTracking/config/advanced/<DEVICE>
```

```
Comment
```

```
Sets <DEVICE> advanced tracking and detection configuration values.
```

```
<DEVICE> The name of the camera device
Persists on system restarts.
```

```
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
detectionMode
```

#### NONE,

#### PERSON,

#### VEHICLE,

#### DRONE,

#### DRONE

#### CLASSIFIED

```
Object detection and tracking
mode for appropriate
application. DRONE or
DRONE CLASSIFED
recommended.
```

```
enableAcquisitionAssist true or false
```

```
System will automatically
resize and change location of
the track box to better acquire
the object.
```

```
enableIntelligentAssist true or false
```

```
System will automatically
reinitialize the object after
detecting a change in the
target appearance.
highNoiseCompensation true or false Enable to improve tracking in
high noise situations.
```

```
maxFrameMiss 1 to 300
```

```
Maximum frames that can be
missed before canceling the
track. Frames is dependent on
autotrackingFPS.
```

```
nearValue 1 to 65535
```

```
Region of interest setting. Can
only detect objects within
nearValue pixel distance
always from past frame’s
object. [not currently in use]
```

```
objectSize 10 to 400
```

```
Size of object in pixels to
track. [not currently in use]
```

```
sensitivity 1 to 10
```

```
Higher value – faster
detection, more likely to
classify object, but with more
false positives.
Valid Response Standard
```

## 3.160. Get Auto Tracking Device PID Configuration.....................................................................................

```
URL GET /modules/autoTracking/config/pid/<DEVICE>
```

```
Comment
```

```
Gets the <DEVICE> active PID configuration values.
```

```
<DEVICE> The name of the camera device
Persists on system restarts.
```

```
Required Data None
```

```
Valid Response
```

```
Ex/
```

```
{"zoom":
"0": {"p": 50, "i":1, "d": 1, "max": 100},
"25": {"p": 35, "i":1, "d": 1, "max": 75},
"50": {"p": 20, "i":1, "d": 1, "max": 50},
"75": {"p": 10, "i":1, "d": 1, "max": 25},
"100": {"p": 1.5, "i":1, "d": 1, "max": 5}
}
```

```
See Set Device PID Configuration for information on returned data.
```

## 3.161. Set Auto Tracking Device PID Configuration

```
URL POST /modules/autoTracking/config/pid/<DEVICE>
```

```
Comment
```

```
Sets the <DEVICE> PID pantilt speed configuration values. Pantilt will select the
PID zoom dictionary, and its PID parameters, corresponding closest to current
zoom level. See Introduction > Pantilt PID Control for more details.
```

```
<DEVICE> The name of the camera device
Persists on system restarts.
```

```
Required Data Format : JSON object
```

```
Parameter Range Description
zoom <str> 0 to 100 Zoom percent in string format
<zoom>
```

```
p int Proportional constant
i int Integral constant
d int Derivative constant
max int Max limit of pantilt percent speed.
```

```
Add new JSON dictionary for more discrete zoom percent and their PID
parameters.
Valid Response Standard
```

## 3.162. Get Auto Tracking Tracks...................................................................................................................

```
URL GET /modules/autoTracking/tracks
```

```
Comment
```

```
Get array of all active tracks observed in current frame, with their metadata.
```

```
Parameter Type Description
```

```
index int Identification of the tracked object. Index of the track
matches the index observed on screen.
is_primary bool Is object being auto tracked by pantilt. Red overlay on
screen.
```

```
is_selected
```

```
bool Is object being selected by pantilt. If object is set to primary,
it is likely it will be selected but not always. Green overlay on
screen. [currently not in use]
```

```
location
```

```
{‘col’:
int,
‘row’:
int}
```

```
In pixels on the screen. Origin is top-left.
```

```
size
```

```
{‘width’:
int,
‘height’:
int}
```

```
In pixels of the tracked object.
```

```
velocity
```

```
{‘col’:
int,
‘row’:
int}
```

```
In pixels/frame. Positive direction is right/down
```

```
confidence Int 0-100: confidence of the object being real
is_coast_state bool If true, object may be lost/trying to recapture
```

```
status
str OFF/BELOW_THRESHOLD/OFF_SCREEN/TRACK_ACTIVE:
predicts if object is likely to be real or off track.
device_key str visible/thermal: Which camera is track observed in.
```

```
classifier_label
```

```
str BACKGROUND/ROTARY WING DRONE/
FIXED WING DRONE/VEHICLE/PERSON/BOAT/
AIRPLANE/UNCLASSIFIED/RESERVED: classification of
object.
classifier_conf int 0-100: confidence of correct classifier_label.
Required
Data None.
```

**Valid
Response**

```
Ex/
[
{
"classifier_conf": 34,
"device_key": "visible",
"is_coast_state": false,
"confidence": 3,
"velocity": {
“col”: -117,
“row”: 10
},
"size": {
“width”: 32,
“height”: 92
},
"status": "TRACK_ACTIVE",
"is_primary": true,
"classifier_label": "FIXED WING DRONE",
"is_selected": true,
"location": {
“col”: 970,
“row”: 552
},
"index": 1
},
{
"classifier_conf": 64,
"device_key": "visible",
"is_coast_state": false,
"confidence": 35,
"velocity": {
“col”: 2349,
“row”: 2971
},
"is_coast_mode": false,
"size": {
“width”: 332,
“height”: 212
},
"status": "OFF",
"is_primary": false,
"classifier_label": "BACKGROUND",
"is_selected": false,
"location": {
“col”: 152,
“row”: 988
```

#### },

```
"index": 3
}
]
```

## 3.163. Initialize Auto Tracking Camera Device

#### URL

```
GET /modules/autoTracking?
command=initializeDevice&camera=<DEVICE>
Comment Performs autotracking initialization for the given DEVICE
Required Data None
Valid Response Standard
```

## 3.164. Start Auto Tracking Target.................................................................................................................

#### URL

```
GET /modules/autoTracking?
command=start&index=<INT>
Comment Start tracking <INT> object. Sets the detected target with the given index as the
active/selected track. This command will overwrite current auto tracking object.
Required Data None
Valid Response Standard
```

## 3.165. Stop Auto Tracking Target.................................................................................................................

```
URL GET /modules/autoTracking?command=stop
Comment Stops any current active auto track and disables enableAutoStartTrack.
Required Data None
Valid Response Standard
```

## 3.166. Autostart Auto Tracking Target.........................................................................................................

#### URL

```
GET /modules/autoTracking?
command=autoStart&classify=<VALUE>
```

```
Comment
```

```
Sets config’s enableAutoStartTrack value to all, drone, vehicle, none, sticky. Allows
for auto start tracking without manually sending start command. If enabled, auto
track with automatically track the object with the highest confidence filtered by
classification.
```

```
See Auto TrackingManual > Optional Features for more details.
```

```
Required Data None
Valid Response Standard
```

## 3.167. Re-Initialize Auto Tracking Device’s Track.........................................................................................

#### URL

```
GET /modules/autoTracking?
command=reinitializeTrack&index=<INT>
```

```
Comment
```

```
Performs a reset <INT> object’s track to optimize its detection and tracking.
Temporarily stops activity for the rest of the system.
```

```
[Currently not in use]
Required Data None
Valid Response Standard
```

## 3.168. Clear Auto Tracking Detections.........................................................................................................

#### URL

```
GET /modules/autoTracking?
command=clearDetections
Comment Clears all on display detections for the device. Does not work in DRONE or
VEHICLE detection mode.
Required Data None
Valid Response Standard
```

## 3.169. Set Auto Tracking Home Position......................................................................................................

#### URL

```
GET /modules/autoTracking?
command=setHomePosition&zoom=<BOOL>&pantilt=<BOOL>
```

```
Comment
```

```
Set current pantilt-zoom position as home position if track is lost. If BOOL is set
to false, turns off home position.
```

```
See Auto Tracking Manual > Optional Features for more details.
Required Data None
Valid Response Standard
```

## 3.170. Get HTTP Panasonic Configuration....................................................................................................

```
URL GET /modules/httpPanasonic/config
Comment Gets the configuration data for the httpPanasonic module
Required Data None
```

```
Valid Response Ex/
{
"initiallyActive": true,
"port": 8222,
"initCheckMax": 20,
"initCheckTimeout": 10
}
```

- **port** defines TCP port for devices to connect to HTTP Panasonic

## 3.171. Get Laser Safety Status......................................................................................................................

```
URL GET /modules/laserSafety/status
Comment Get status data about Laser Safety module. See ZLID safety guide for more
information.
Required Data None
Valid Response Ex/
{
"safetyLockEnabled": true,
"insidePanSafety": false,
"insideTiltSafety": true,
"previousPowerState": “OFF”,
"previousZoomLevel": 50
}
```

- **safetyLockEnabled** defines if laser safetyMode is on
- **insidePanSafety** defines if pan position is within the safe operating range
- **insideTiltSafety** defines if tilt position is within the safe operating range
- **previousPowerState** saves last power state that will be enabled once
  safetyLockEnabled is false
- **previousZoomLevel** saves last zoom level state that will be enabled once
  safetyLockEnabled is false

## 3.172. Get Laser Safety Configuration..........................................................................................................

```
URL GET /modules/laserSafety/config
Comment Gets the configuration for the Laser Safety module.
```

```
Range between minTilt/maxTilt and minPan/maxPan is normal operating range.
Outside of the normal operating range, the ZLID safetyMode is applied. The laser
will return to previous state (on or ZLID zoom level) when re-entering the normal
operating range.
```

```
See ZLID safety guide for more information.
Required Data None
Valid Response Ex/
{
"minTilt": -15,
"maxTilt": 15,
"minPan": 0,
"maxPan": 100,
"safetyMode": “OFF”,
}
```

## 3.173. Set Laser Safety Configuration

```
URL POST /modules/laserSafety/config
Comment Sets the configuration for the Laser Safety module.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
minTilt -90 to 90
```

```
Range lower than minTilt is unsafe
operating range and applies laser
safety. Range higher than minTilt is
normal operating range.
```

```
maxTilt -90 to 90
```

```
Range higher than maxTilt is unsafe
operating range and applies laser
safety. Range lower than maxTilt is
normal operating range.
```

```
minPan 0 to 360
```

```
Range counterclockwise of minPan to
maxPan is unsafe operating range
and applies laser safety. Range
between minPan and maxPan is
normal operating range.
```

```
maxPan 0 to 360
```

```
Range clockwise of maxPan to
minPan is unsafe operating range and
applies laser safety. Range between
minPan and maxPan is normal
operating range.
```

```
safetyMode OFF or WIDE
```

```
OFF: turns off laser
WIDE: diverge to widest angle (0
zoom)
```

```
Valid Response Standard
```

## 3.174. Laser Sync

**IMPORTANT –** This section on laser synchronization is only relevant to supported model combinations.
Certain synchronizations require a more advanced calibration that cannot be accomplished via these API
calls. In this case, calling GET /modules/laserSync/config will only manage the ‘override’ and
‘initiallyActive’ parameters. Please contact Infiniti if calibration of laser sync is required.

## 3.175. Get Laser Sync Configuration

```
URL GET /modules/laserSync/config
Comment Gets the configuration for the Laser Sync module.
```

```
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"override": false
}
```

## 3.176. Set Laser Sync Configuration.............................................................................................................

```
URL POST /modules/laserSync/config
Comment Sets the configuration for the Laser Sync module.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
override true or false
```

```
Indicates whether the
ZLID zoom level can
be adjusted while the
visible lens is not
moving
Valid Response Standard
```

## 3.177. Get Lifecycle Tracker Status

```
URL GET /modules/lifecycleTracker/status
Comment Gets the current state data for the lifecycle values of this system
Required Data None
```

```
Valid Response Ex/
{
"system": {
"currentUptime": "3 hours, 11 minutes",
"initializationAttempts": 24,
"totalLifetime": "203d 13:09:57"
},
"thermal": {
"currentInitializationTime": "05:33",
"initializationTimeAverage": "05:22",
"initializationTimeTotal": "0d 08:43:15",
"initializationAttempts": 21,
"totalLifetime": "184d 06:59:32"
}
}
```

## 3.178. Get Lifecycle Tracker Configuration

```
URL GET /modules/lifecycleTracker/config
Comment Gets the configuration data for the lifecycleTracker module
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"updateInterval": 60,
"thermalInitCheckInterval": 5
}
```

```
See Set Lifecycle Tracker Configuration for more information on returned data
```

## 3.179. Set Lifecycle Tracker Configuration...................................................................................................

```
URL POST /modules/lifecycleTracker/config
Comment Sets the configuration data for the lifecycleTracker module
```

```
Required Data
```

```
Parameter Description Range
updateInterval Seconds between each update cycle 10 to 3600
thermalInitCheckInterval Seconds between each status check
while the thermal is initializing
```

```
1 to 60
```

```
Valid Response Standard
```

## 3.180. Pelco System Controller

The Pelco System Controller module is a process running on the Octagon platform that interprets
incoming Pelco-D commands and sends out the corresponding device commands. Because Pelco-D is a
general protocol not created by Infiniti, only certain devices within the system can be controlled via
Pelco-D. Even the devices that can be affected will only have their basic functionality available through
this method. Typically, Pelco-D commands are sent to the system via RS485 or other external serial
connections.

Pelco-D provides an extensible command system called ‘Presets’. Each preset command is accompanied
by an **ID** byte value (1 – 254). The first 79 **ID** values (1 – 79) are used similarly to the
/api/system/presets section of this API. They SET, CLEAR, and CALL the positions of the **pantilt** and any
supported camera devices. These IDs share common storage to the presets API. Presets above 80 are
reserved by Infiniti for specific functionality, to be used for debugging or if the user does not have
ethernet access to the Octagon API. All Pelco-D preset functionality is also available via the API. In other
words, the Pelco System Controller does not add any commands or functionality to the system, it only
exposes some of them through an alternative method.

For more information regarding Pelco-D compatibility or custom development of a preset command list,
contact Infiniti directly.

## 3.181. Get Pelco System Controller Configuration.......................................................................................

```
URL GET /modules/pelcoSystemController/config
Comment Gets the configuration information for the Pelco System Controller module.
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"sourceDevices": {
"api": {
"priority": 4,
"enabled": true
},
"pelnetReceiver": {
"priority": 1,
"enabled": true
},
"externalPrimary": {
"priority": 3,
"enabled": true
},
"externalSecondary": {
"priority": 2,
"enabled": true
```

#### },

```
"tcpPelcoReceiver": {
"priority": 5,
"enabled": true
}
```

```
},
"outputDevices": {
"pantilt": true,
"visible": true,
"thermal": true,
"zlid": false,
"swir": true
},
"addresses": {
"visible": 1,
"zlid": 1,
"thermal": 2,
"swir": 3
},
"defaultPanSpeedFraction": 0.3,
"defaultTiltSpeedFraction": 0.3,
"panSpeedFraction": 0.2,
"panSpeedMin": 0.001,
"panSpeedMax": 1.0,
"tiltSpeedFraction": 0.2,
"tiltSpeedMin": 0.001,
"tiltSpeedMax": 1.0,
"proportionalMode": "visible",
"magnificationInterpretation": "focus"
}
See Set Pelco System Controller Configuration for information on returned data.
```

## 3.182. Set Pelco System Controller Configuration

```
URL POST /modules/pelcoSystemController/config
Comment Sets the configuration data for the Pelco System Controller module
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
sourceDevices
```

```
This list of Octagon devices controls which
interfaces can send their Pelco D commands as
input to this module. Most often they can all be
```

```
left enabled, when disabled the system will ignore
any commands received
```

```
Available keys are api , pelnetReceiver ,
externalPrimary , externalSecondary ,
externalTertiary, and tcpPelcoReceiver
```

outputDevices

```
Similar to input devices, this list controls which
Octagon devices (components) can be controlled
by this module. If set to false, then no commands
will be sent to that device via this module, but it
will still accept commands from other sources. For
most situations, these can be all left to true
(enabled)
```

```
Available keys are pantilt , visible , thermal , zlid ,
and swir
```

addresses 1 to 254

```
The Pelco-D address that
corresponds to each available
outputDevice. Note that thermal,
visible, and SWIR cannot share
addresses
```

```
Required keys are visible , zlid,
thermal , and swir
```

pan/tiltSpeedFraction 0.00001 to 1

```
Applied to input speed to produce
motor output speed
```

pan/tiltSpeedMin 0.00001 to 1

```
The minimum allowed motor
speeds
```

pan/tiltSpeedMax 0.00001 to 1

```
The maximum allowed motor
speeds
```

defaultPan/TiltSpeedFraction 0.00001 to 1

```
When using Special Function
Preset 83, resets speed fractions
to these values
```

magnificationInterpretation

```
Controls how Pelco D commands SET
MAGNIFICATION (0x5f) and QUERY
MAGNIFICATION (0x61) are handled
```

```
zlid – Get and set ZLID collimator position
focus – Get and set focus of addressed lens
```

proportionalMode

```
This parameter defines what the proportional
adjustments of pan tilt speed are based on, and
can take the following values:
```

```
visible - The visible lens exclusively
thermal - The thermal lens exclusively
swir – The SWIR lens exclusively
narrowest - The narrowest of the thermal or
visible lenses
```

```
widest - The widest of the thermal or visible
lenses
recent - The lens that was most recently adjusted
Valid
Response
Standard
```

## 3.183. Send Pelco-D Commands Directly

```
URL GET /modules/pelcoSystemController?send=<DATA>
```

```
Comment Emulates a Pelco-D device by sending the given DATA to this module. See Pelco
D Protocol Version 5.2.7 for information about specific Pelco-D commands.
Required Data The Pelco-D data to send to this module. Data must be formatted as 2-character
HEX strings. Ex/ FF010002200023 (pan right). The checksum must be correct, or
an error message will be displayed.
Valid Response Standard
```

## 3.184. Get Power Conserve Status...............................................................................................................

```
URL GET /modules/powerConserve/status
Comment Gets the status of the powerConserve module, including what commands are
configured for execution on this system
Required Data None
Valid Response Ex/
{
"nextShutoff": "2020-04-04T17:30:00.000000",
"checkInterval": 15,
"lastShutoff": "2020-04-03T17:31:54.380780",
"timeToShutoff": "19:36:07",
"actions": [
"gyro off",
"defrost off"
]
}
```

```
Note that the list of tasks executed by this module is device dependent and will
vary between systems
```

## 3.185. Get Power Conserve Configuration...................................................................................................

```
URL GET /modules/powerConserve/config
```

```
Comment Gets the configuration data for the powerConserve module
Required Data None
```

```
Valid Response Ex/
{
"initiallyActive": true,
"checkInterval": 15,
"shutoffTime": "17:30"
}
```

```
See Set Power Conserver Configuration for more information on returned data
```

## 3.186. Set Power Conserve Configuration....................................................................................................

```
URL POST /modules/powerConserve/config
Comment Sets the configuration data for the powerConserve module
```

```
Required Data
```

```
Parameter Description Range
checkInterval Time in seconds between each check for
shutoffTime trigger
```

```
1s to 100,000s
```

```
shutoffTime Time of day to schedule the shutoff event,
occurs every day unless this module is
disabled.
```

#### HH:MM

```
(24-hour clock)
```

```
Valid Response Standard
```

### 3.187. Set Power Conserve Shutoff Time.....................................................................................................

```
URL POST /modules/powerConserve?command=setShutoffTime&time=<HH:MM>
Comment Sets the shutoff time for the powerConserve module
```

```
Required Data
```

```
Time of day to schedule the shutoff event, occurs every day unless this module is
disabled.
```

```
HH:MM
(24-hour clock)
```

```
Valid Response Standard
```

### 3.188. Get Processing Toggle Configuration

```
URL GET /modules/processingToggle/config
Comment Gets the configuration data for the processingToggle module
```

```
Required Data
```

```
Ex/
```

```
{
```

```
initiallyActive: true,
timeoutFactor: {
pantilt: 0.08,
thermal: 0.05,
visible: 0.05,
swir: 0.05,
},
reactivateDelay: 1.5
events: [
AMOVE,
RMOVE,
SET,
TELE,
WIDE
],
eventLenses: ["thermal", "swir"]
}
```

```
See Set Processing Toggle Configuration for more information on returned data
Valid Response Standard
```

### 3.189. Set Processing Toggle Configuration.................................................................................................

```
URL POST /modules/processingToggle/config
Comment Sets the configuration data for the processingToggle module
```

```
Required Data
```

```
Parameter Description Range
timeoutFactor Available keys are pantilt , thermal, visible, and swir.
These values are configured at factory according to the
component models. They define how long to wait for
absolute movement commands before resuming the
processing features. pantilt is required while all others
all optional
reactivateDelay Time between the last pantilt or lens
command and when the video
processing with be reactivated. Added
onto the initial delay calculated using
timeoutFactor
```

```
0s to 100s
```

```
events Events that will cause the video
processing to be disable for the
timeout duration.
```

#### RPAN,

#### RTILT,

#### RMOVE,

#### AMOVE,

#### STOP, SET,

#### TELE, WIDE,

```
or
ZOOM_STOP
eventLenses List of lenses can raise the events. Possible values
include thermal , visible , and swir
Valid Response Standard
```

### 3.190. Get TCP Pelco Receiver Configuration...............................................................................................

```
URL GET /modules/tcpPelcoReceiver/config
Comment Gets the configuration data for the tcpPelcoReceiver module
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"port": 8005,
"maxConnections": 10,
"controlLockTimeout": 5.0,
"pollInterval": 0.5
}
```

```
See Set TCP Pelco Receiver Configuration for more information on returned data
```

### 3.191. Set TCP Pelco Receiver Configuration

```
URL POST /modules/tcpPelcoReceiver/config
Comment Sets the configuration data for the tcpPelcoReceiver module
```

```
Required Data
```

```
Parameter Description Range
port Port used to communicate with the TCP
server
```

```
0 to 65535
```

```
maxConnections How many concurrent connections are
tolerated by the server
```

```
1 to 100
```

```
controlLockTimeout Control is locked to last active client for
this duration before it will accept
commands from another
```

```
0s to 360s
```

```
pollInterval Keep alive message interval 0s to 360s
```

```
Valid Response Standard
```

### 3.192. Get TCP Visca Keyboard Configuration..............................................................................................

```
URL GET /modules/tcpViscaKeyboard/config
Comment Gets the configuration data for the tcpViscaKeyboard module
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"port": 8007,
"maxConnections": 10,
"controlLockTimeout": 5.0,
"pollInterval": 0.5
}
```

- **port** defines TCP port for devices to connect to Visca Keyboard

### 3.193. Get Thermal Sync Configuration........................................................................................................

```
URL GET /modules/thermalSync/config
Comment Gets the configuration for the Thermal Sync module.
```

```
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"override": false,
"syncSteps": [
{ "visible": 30, "thermal": 20 },
{ "visible": 35, "thermal": 20 },
{ "visible": 40, "thermal": 20 },
{ "visible": 45, "thermal": 25 },
{ "visible": 50, "thermal": 30 },
{ "visible": 55, "thermal": 35 },
{ "visible": 60, "thermal": 40 },
{ "visible": 65, "thermal": 45 },
{ "visible": 70, "thermal": 50 },
{ "visible": 75, "thermal": 55 },
{ "visible": 80, "thermal": 60 },
{ "visible": 85, "thermal": 65 },
{ "visible": 90, "thermal": 80 },
{ "visible": 95, "thermal": 80 },
{ "visible": 100, "thermal": 80}
]
```

#### }

### 3.194. Set Thermal Sync Configuration

```
URL POST /modules/thermalSync/config
Comment Sets the configuration for the Thermal Sync module.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
override true or false
```

```
Indicates whether the
thermal zoom level
can be adjusted while
the visible lens is not
moving
```

```
syncSteps
```

```
Array of {“visible”:
[zoom_level],
“thermal”:
[zoom_level]
```

```
Determines the level
of thermal zoom
associated with the
level of visible zoom
Valid Response Standard
```

### 3.195. Get Light Sync Configuration.............................................................................................................

```
URL GET /modules/lightSync/config
Comment Gets the configuration for the Light Sync module.
```

```
Required Data None
Valid Response Ex/
{
"initiallyActive": true,
"override": false,
"syncSteps": [
{ "lens": 30, "light": 30 },
{ "lens": 35, "light": 35 },
{ "lens": 40, "light": 40 },
{ "lens": 45, "light": 45 },
{ "lens": 50, "light": 60 },
{ "lens": 55, "light": 70 },
{ "lens": 60, "light": 80 },
{ "lens": 65, "light": 82 },
{ "lens": 70, "light": 85 },
{ "lens": 75, "light": 89 },
{ "lens": 80, "light": 90 },
{ "lens": 85, "light": 91 },
```

```
{ "lens": 90, "light": 92 },
{ "lens": 95, "light": 92 },
{ "lens": 100, "light": 92 }
]
}
```

### 3.196. Set Light Sync Configuration..............................................................................................................

```
URL POST /modules/lightSync/config
Comment Sets the configuration for the Light Sync module.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
override true or false
```

```
Indicates whether the
thermal zoom level
can be adjusted while
the visible lens is not
moving
```

```
syncSteps
```

```
Array of {“lens”:
[zoom_level], “light”:
[zoom_level]
```

```
Determines the level
of light zoom
associated with the
level of visible zoom
Valid Response Standard
```

### 3.197. Get Custom OSD Overlay Configuration............................................................................................

```
URL GET /modules/customOSDOverlay/config
Comment Gets the configuration for the Custom OSD Overlay module.
```

```
Required Data None
Valid Response Ex/
{
"display_focus_mode": true,
"display_EIS": true,
"display_color_palette": true,
“display_zlid_state”: false,
“display_lrf_range”: false,
"initiallyActive": true
}
```

### 3.198. Set Custom OSD Overlay Configuration

```
URL POST /modules/customOSDOverlay/config
```

```
Comment Sets the configuration for the Custom OSD Overlay module.
Required Data Format : JSON object
```

```
Parameter Range Description
```

```
display_focus_mode true or false
```

```
Display Focus mode
on OSD
```

```
display_EIS true or false
```

```
Display stabilization
state on OSD
```

```
display_color_palette true or false
```

```
Display current solor
palette on OSD
```

```
display_zlid_state true or false
```

```
Display zlid state on
OSD (if zlid present)
```

```
Display_lrf_range true or false
```

```
Display lrf range on
OSD (if lrf present)
Valid Response Standard
```

### 3.199. Get Peripherals..................................................................................................................................

```
URL GET /peripherals
Comment Gets the current status for all peripherals.
Required Data None
Valid Response Ex/
{
"wiper": {
"active": false,
},
"washer": {
"active": false,
},
"defrost": {
"active": true,
}
}
```

```
Exact meaning of 'active' parameter is dependent on peripheral type, mode, and
model
```

### 3.200. Get Peripheral State

```
URL GET /peripherals/<PERIPHERAL>
Comment Get the status (active or not) for any peripheral
Required Data None
```

```
Valid Response Ex/
{
"active": false
}
```

### 3.201. Turn Defrost On / Off.........................................................................................................................

```
URL GET /peripherals/defrost?command=<activate OR deactivate>
Comment Turn the defrost on or off.
Required Data None
Valid Response Standard
```

### 3.202. Get Defrost Config.............................................................................................................................

```
URL GET /peripherals/defrost/config
Comment Gets the current configuration data for the defrost system
Required Data None
```

```
Valid Response Ex/
{
"duration": 300,
"mode": "PERMANENT"
}
See Set Defrost Configuration for information on returned data.
```

### 3.203. Set Defrost Configuration..................................................................................................................

```
URL POST /peripherals/defrost/config
Comment Sets the configuration values for the defrost system.
Required Data Format: JSON object
```

```
Parameter Description Range
duration How long in seconds the defrost
should remain active before
shutting off. Only applies in
"DURATION" mode
```

```
1s to 86400s
```

```
mode Defrost operation mode PERMANENT or DURATION
```

```
Valid Response Standard
```

### 3.204. Get Photocell Status

```
URL GET /peripherals/photocell/status
```

```
Comment Gets the photocell's current reading, as well as a true/false day value indicating
whether it reads day or night.
Required Data None
Valid Response Ex/
{
"currentValue": 86%,
"day": true
}
```

```
currentValue ─ The percentage of light read by the photocell, with lower
numbers corresponding to lower light levels and vice versa.
```

```
day ─ Whether or not the system is in day mode. If day is false, the system is in
night mode.
```

### 3.205. Get Photocell Configuration..............................................................................................................

```
URL GET /peripherals/photocell/config
Comment Gets the configuration data for the photocell.
Required Data None
Valid Response Ex/
{
"changeThreshold": 5,
"triggerSeconds": 10,
"dayNightBoundary": 60
}
```

```
See Set Photocell Configuration for information on returned data.
```

### 3.206. Set Photocell Configuration...............................................................................................................

```
URL POST /peripherals/photocell/config
Comment Sets the configuration value for the photocell.
Required Data Format: JSON object
```

```
Parameter Description Range
dayNightBoundary The point above which is considered day, and
below which is considered night
```

```
0 to
100%
```

```
changeThreshold Padding around the dayNightBoundary to
prevent alternating between day and night if
the photocell value is hovering around that
value. 5%, for example, forces the photocell
to read at least 5% below the
dayNightBoundary before it changes to night,
and at least 5% above before it changes to
day.
```

```
1% to
99%
```

```
triggerSeconds Seconds duration that the photocell readings
must stay above or below the
dayNightBoundary before the day/night
value changes
```

```
0 to 120
```

```
Valid Response Standard
```

### 3.207. Turn Power Switch On / Off...............................................................................................................

```
URL GET /api/peripherals/powerSwitch?command=<activate OR deactivate>
Comment Turn the powerSwitch on or off.
Required Data None
Valid Response Standard
```

### 3.208. Get Power Switch Configuration

```
URL GET /peripherals/powerSwitch/config
Comment Gets the configuration data for the powerSwitch.
Required Data None
Valid Response Ex/
{
"description": "ZLID diode"
}
```

### 3.209. Turn Thermal Circuit On / Off............................................................................................................

```
URL GET /api/peripherals/thermalCircuit?command=<activate OR deactivate>
```

```
Comment
```

```
When systems are built with a separate power circuit for the thermal enclosure,
this command turns this circuit on or off. It is important to note there is a
mandatory ‘reactivate delay’ period (default 30 seconds) that prevents toggling
the power on and off too rapidly, which can be unsafe for high-value devices.
Despite this safeguard, this command should be used with extreme caution and
care.
Required Data None
```

**Valid Response** Standard

### 3.210. Get Thermal Circuit Configuration

```
URL GET /peripherals/thermalCircuit/config
Comment Gets the configuration data for the thermalCircuit.
Required Data None
Valid Response Ex/
{
"triggerOnStartup": false,
"reactivateThreshold": 60,
}
```

### 3.211. Set Thermal Circuit Configuration

```
URL POST /peripherals/thermalCircuit/config
Comment Sets the configuration values for the thermalCircuit.
Required Data Format: JSON object
```

```
Parameter Description Range
triggerOnStartup Start thermal circuit on power start up true or false
reactivateThreshold Mandatory ‘reactivate delay’ period
(default 30 seconds) that prevents
toggling the power on and off too
rapidly
```

```
5s to 6000s
```

```
Valid Response Standard
```

### 3.212. Turn Washer On / Off........................................................................................................................

```
URL GET /peripherals/washer?command=<activate OR deactivate>
&movePantilt=<true OR false>
```

```
Comment
```

```
Turn the washer on or off.
```

```
movePantilt can optionally be set to false to disable to pre-spray pantilt
movement. This defaults to true
Required Data None
Valid Response Standard
```

### 3.213. Get Washer Configuration.................................................................................................................

```
URL GET /peripherals/washer/config
Comment Gets the configuration data for the washer.
Required Data None
Valid Response Ex/
{
"washTime": 2,
"wipeTime": 10,
"pantiltPosition": { "pan": 45, "tilt": -20 },
"pantiltMoveDelay": 7,
"wipeDelay": 7
}
```

```
See Set Washer Configuration for information on returned data.
```

### 3.214. Set Washer Configuration

```
URL POST /peripherals/washer/config
Comment Sets the configuration values for the washer.
Required Data Format: JSON object
```

```
Parameter Description Range
washTime How long washer fluid will be applied
for in seconds.
```

```
1s to 10s
```

```
wipeTime How long the wiper will run for in
seconds.
```

```
1s to 300s
```

```
pantiltPosition Absolute position the pantilt will be set
to before startingthe wash sequence.
pantiltMoveDelay Time for the pantilt to reach the
pantiltPosition before starting the
washer sequence
```

```
1s to 20s
```

```
wipeDelay Time for washer spray to reach optics
before starting wiper
```

```
1s to 20s
```

```
Valid Response Standard
```

### 3.215. Turn Wiper On / Off...........................................................................................................................

```
URL GET /peripherals/wiper?command=<activate OR deactivate>
Comment Turn the wiper on or off.
Required Data None
```

```
Valid Response Standard
Get Defrost State GET /peripherals/defrost
```

### 3.216. Turn IR On / Off / auto.......................................................................................................................

```
URL GET /peripherals/ir?command=<activate OR deactivate OR auto>
```

```
Comment Turn the ir on or off or set to auto (control by photocell). Not supported on all
series or models
Required Data None
Valid Response Standard
```

### 3.217. Get IR Status

```
URL GET /peripherals/IR/status
Comment Gets the IRs current mode (AUTO / MANUAL).
Required Data None
Valid Response Ex/
{
"MODE": “AUTO”
}
```

```
Mode ─ if set to Auto mode then depending on photocell it with turn on or off, if
set to Manual mode then functionality of switching automatic will be blocked and
can be control from activate/deactivate command.
```

## 4. Support and Custom Development...............................................................................................................

The OCTAGON HTTP API is a continuous, dynamic platform that always has updates and extensions on
the go. This document is the most recent and complete description of this interface, but it by no means
expresses the complete scope of Infiniti or Ascendent system capabilities. If you are looking for a
functionality or device not found here, it may be in development, or already developed but not released
as part of our public API. Do not hesitate to contact us and find out about our custom development
options.

This platform is built with the big picture in mind. We understand that many use-cases involve
integrating with existing modern or legacy devices, protocols, and frameworks. Infiniti is ready to quote
services such as rapid-prototyping, unique module development, and system architecting to ensure our
system can meet the specific needs of your use-case. Infiniti has a uniquely postured R&D division that
is geared towards flexibility, low time-to-market, and creative solutions to meet advanced industry
scenarios. Custom solutions are what we do best.

If you have further questions about our API or are interested in pursuing further partnership, please
contact Infiniti Optics directly.

## 5. Disclaimer......................................................................................................................................................

Infiniti shall not be liable for any damages, including, without limitation, direct, indirect, incidental,
special, reliance, or consequential damages arising from improper or unwarranted use of the above API
and associated hardware in any manner whatsoever. Infiniti does not warrant that the above API and
associated hardware are error-free, nor does Infiniti make any other representations or warranties,
whether express or implied, statutory or otherwise, including, but not limited to, implied warranties of
merchantability, fitness for a particular purpose, or noninfringement.
