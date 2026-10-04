# BioLite FirePit Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)

Custom Home Assistant integration for controlling the **BioLite FirePit / FirePit+** via Bluetooth LE (using Home Assistant BLE Proxies or local Bluetooth adapters).

## Features

- **Fan Control (`fan` entity)**: Control airflow fan speed (`Off`, `Low`, `Medium`, `High`, `Max`).
- **USB Charger (`switch` entity)**: Toggle power to the USB powerpack output port.
- **Sensors (`sensor` entities)**: Monitor FirePit battery percentage.
- **BLE Proxy Support**: Fully compatible with ESPHome BLE proxies and Home Assistant Bluetooth proxies.

## Installation via HACS

1. Open **HACS** in your Home Assistant sidebar.
2. Click the 3 dots in the top right corner and select **Custom repositories**.
3. Paste the URL of your GitHub repository into the **Repository** field.
4. Select **Integration** as the Category.
5. Click **Add**, then find **BioLite FirePit** in HACS and click **Download**.
6. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **BioLite FirePit**.
3. Enter your FirePit's Bluetooth MAC Address (e.g. `AA:BB:CC:DD:EE:FF`).
