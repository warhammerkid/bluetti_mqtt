# Change Log

## FUTURE

* Fix bug in logging multiple batteries where the last slot was skipped.

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
