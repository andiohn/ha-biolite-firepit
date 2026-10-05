# BioLite FirePit Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)

Home Assistant integration for controlling the BioLite FirePit / FirePit+ over Bluetooth Low Energy (BLE) proxy.

## Features
- **Fan Control**: Off (0%), Low (25%), Med (50%), High (75%), On/Max (100%).
- **USB Charger Switch**: Toggle USB power output on/off.
- **Battery Sensor**: Monitor remaining powerpack battery percentage.
- **Temperature Sensor**: Monitor firebox temperature (°F).

## Installation
1. Install via HACS (Custom Repository) or copy `custom_components/biolite_firepit` into your Home Assistant `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & Services -> Add Integration** and select **BioLite FirePit**.
4. Enter your FirePit's BLE MAC Address.
