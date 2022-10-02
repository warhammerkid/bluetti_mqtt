# Change Log

## FUTURE

* Add LED status and setting to homeassistant for EB3A (@ray0711)
* Fix crash with failed bluetooth connection
* Add beta support for AC500

## 0.8.3

* Fix a bug with `dc_input_power` reporting

## 0.8.2

* More bug fixes...

## 0.8.1

* Fix build issue

## 0.8.0

* Add support for reporting details for multiple battery packs
* Re-architect internals for a better logical separation into layers (core, bluetooth, and the polling + MQTT app)

## 0.7.1

* Fix crash with EB3A logging (@jretz)

## 0.7.0

* Add support for Home Assistant discovery (@lbossle)
* Re-architect parsing to support device-specific customization
* Add beta support for EB3A
* Fix bug with automatic bluetooth reconnect

## 0.6.3

* Fix bug with scanning unnamed devices for WinRT bluetooth backend
* Fix bug with converting commands to bytes for WinRT & macOS blueooth backend
* Fix issue with using an unsupported event loop on Windows for asyncio-mqtt

## 0.6.2

* Fix bug in logging multiple batteries where the last slot was skipped.
* Automatically reconnect to broker if disconnected

## 0.6.1

* Added support for paging through batteries in the logger to collect more information about how things work.

## 0.6.0

* Added support for configuring username / password / port for MQTT broker
* Added proper signal handling. It now correctly shuts down when sent SIGTERM or SIGINT.

## 0.5.1

* Added a `DEBUG` environment variable that turns on more logging

## 0.5.0

* Started parsing out more fields from the device
* Added support for handling invalid request errors

## 0.4.0

* Added an `--interval` command line flag to change the polling rate

## 0.3.0

* Added support for sending commands to the device over MQTT
