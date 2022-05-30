============
bluetti_mqtt
============

This tool provides an MQTT interface to Bluetti power stations. State will be
published to the `bluetti/state/[DEVICE NAME]/[PROPERTY]` topic, and commands
can be sent to the `bluetti/command/[DEVICE NAME]/[PROPERTY]` topic.

Installation
------------

.. code-block:: bash

    $ pip install bluetti_mqtt

Usage
-----

.. code-block:: bash

    $ bluetti-mqtt --scan
    Found AC3001234567890123: address 00:11:22:33:44:55
    $ bluetti-mqtt --broker [MQTT_BROKER_HOST] 00:11:22:33:44:55

Logging
-------

For research purposes you can also use the `bluetti-logger` command to poll the
device and log in a standardised format.

.. code-block:: bash

    $ bluetti-logger --log the-log-file.log 00:11:22:33:44:55
