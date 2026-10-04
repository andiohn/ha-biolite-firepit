import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from bleak import BleakClient

from .const import (
    DOMAIN,
    BATTERY_LEVEL_CHARACTERISTIC_UUID,
    BATTERY_PERCENT_CHARACTERISTIC_UUID,
    TEMPERATURE_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([
        BioLiteBatterySensor(hass, mac),
        BioLiteTemperatureSensor(hass, mac),
    ])

class BioLiteBatterySensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, hass, mac):
        self.hass = hass
        self._mac = mac
        self._attr_unique_id = f"{mac}_battery"
        self._attr_native_value = None

    async def async_update(self) -> None:
        """Fetch battery percentage from BioLite powerpack over BLE."""
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            _LOGGER.warning("BioLite FirePit BLE device not found for battery update (%s)", self._mac)
            return

        try:
            async with BleakClient(device) as client:
                val = None
                # Try vendor specific battery percent characteristic
                try:
                    raw = await client.read_gatt_char(BATTERY_PERCENT_CHARACTERISTIC_UUID)
                    if raw and len(raw) > 0:
                        val = int(raw[0])
                except Exception:
                    pass

                # Fallback to standard BLE battery level characteristic
                if val is None:
                    try:
                        raw = await client.read_gatt_char(BATTERY_LEVEL_CHARACTERISTIC_UUID)
                        if raw and len(raw) > 0:
                            val = int(raw[0])
                    except Exception as err:
                        _LOGGER.debug("Failed reading standard battery level: %s", err)

                if val is not None and 0 <= val <= 100:
                    self._attr_native_value = val
                    _LOGGER.debug("Updated BioLite battery level: %d%%", val)
        except Exception as err:
            _LOGGER.error("Error reading battery level over BLE from %s: %s", self._mac, err)


class BioLiteTemperatureSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def __init__(self, hass, mac):
        self.hass = hass
        self._mac = mac
        self._attr_unique_id = f"{mac}_temperature"
        self._attr_native_value = None

    async def async_update(self) -> None:
        """Fetch firebox temperature from BioLite powerpack over BLE."""
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            return

        try:
            async with BleakClient(device) as client:
                raw = await client.read_gatt_char(TEMPERATURE_CHARACTERISTIC_UUID)
                if raw and len(raw) > 0:
                    temp_f = float(raw[0]) - 32.0
                    self._attr_native_value = round(temp_f, 1)
        except Exception as err:
            _LOGGER.debug("Error reading temperature over BLE from %s: %s", self._mac, err)
