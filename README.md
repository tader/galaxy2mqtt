# galaxy2mqtt

## Setup

- Clone this repository in /share/galaxy2mqtt
  `git clone git@github.com:tader/galaxy2mqtt.git /share/galaxy2mqtt`
- Copy the home assistant addon
  `cp -a /share/galaxy2mqtt/homeassistant /addons/galaxy2mqtt`
- In the Home Assistant Supervisor Add-on Store, click the three-dots menu, Reload
- In Local add-ons, find Galaxy2mqtt, click Install
- Once installed, in its Configuration pane, configure the MQTT credentials, devices, and serial port.

## Example config

```yaml
mqtt:
  base_discovery_topic: homeassistant
  base_topic: galaxyrs485
  server: core-mosquitto
  user: homeassistant
  password: super secret
devices:
  - type: Keypad
    address: 16
  - type: RFPortal
    address: 133
serial:
  port: /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A10KM84B-if00-port0
availability: {}
web: {}
```
