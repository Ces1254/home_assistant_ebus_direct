#Home Assistant eBus Direct Integration

A Home Assistant custom integration that communicates directly with ebusd to monitor heating systems connected to an eBus network, with a focus on operational analysis, logging, and efficiency monitoring.
This integration is designed primarily for heat pump performance monitoring, not for system control.

##Overview

Most Home Assistant setups use the following architecture:

    eBus → ebusd → MQTT → Home Assistant


While this works well for standard installations, it introduces:
* additional infrastructure (MQTT broker)
* fixed polling logic
* limited control over message decoding
* difficulty handling multi-message or freshness-based sensors
This integration instead connects directly to ebusd over its TCP interface and builds Home Assistant entities from:
* find queries
* read commands
* custom decoding logic

##Design Goals

The integration was developed with the following priorities.
1) Monitoring rather than control
    The primary goal is:
    * logging operational parameters
    * monitoring system performance
    * tracking energy flows
    * analyzing efficiency (COP, power balance, etc.)
    It is not intended to control the heating system. Operational changes such as:    
    * switching the system on/off
    * changing schedules
    * modifying comfort settings
    are usually better handled through the vendor’s official app or controller, which:
    * knows system constraints
    * enforces safe operating limits
    * avoids unintended states

2) Direct ebusd communication
    The integration:
    * connects directly to the ebusd TCP interface
    * avoids MQTT entirely
    * issues find and read commands as needed
    This allows:
    * per-sensor logic
    * dynamic message selection
    * reduced system complexity

3) Freshness-aware sensors
    Sensors can:
    * prefer recently broadcast messages
    * fall back to direct reads if needed
    * discard stale data
    This is useful for:
    * cyclic broadcast values
    * parameters not always present on the bus

4) Custom decoding support
    The integration supports:
    * raw hex message decoding
    * scaling factors
    * offsets
    * custom decoder logic
    This makes it suitable for:
    * reverse-engineered devices
    * non-standard parameters
    * systems with incomplete ebusd definitions

##Target Use Cases

This integration is intended for:
* advanced Home Assistant users
* heat pump owners interested in performance monitoring
* users reverse-engineering eBus devices
* installations without MQTT infrastructure
* custom or experimental sensor setups

##Key Features

* Direct TCP connection to ebusd
* No MQTT required
* Per-sensor find vs read logic
* Freshness-based message selection
* Custom decoding of raw messages
* Flexible sensor definitions
* Optimized for heat pump performance monitoring

##Requirements

* Home Assistant (tested with recent Core versions)
* Running ebusd instance with TCP access enabled

Typical setup:

eBus → ebusd → Home Assistant (this integration)

##Installation
Manual installation
Copy the integration folder into:

    <config>/custom_components/ebus_direct/

Prepare your entities description by editing the yaml configuration file.
Restart Home Assistant.
Add the integration via:
    Settings → Devices & Services → Add Integration

##Configuration

Sensors are defined through a configuration structure that includes:

* eBus command or tag
* unit
* device class
* freshness limits

Example
sensors:
  flow_temp:
    name: "Flow Temperature"
    ebus_find_tag: "OP010,OP042"
    scale: 0.1
    unit: "°C"
    device_class: temperature
    max_age: 180

##Important Notes

This integration is primarily read-only on eBus.
Write operations are intentionally absent.
System control should normally be done via the manufacturer’s controller or app.

##Status

Actively developed
Tested on systems using ebusd
Initial focus on heat pump monitoring

##Contributing

Contributions are welcome, especially:
* additional sensor definitions
* decoders for other eBus devices
* testing on different systems

##Disclaimer

This project is:
* not affiliated with any heating system manufacturer
* not an official ebusd component
* provided as-is, without warranty

###Use at your own risk.
