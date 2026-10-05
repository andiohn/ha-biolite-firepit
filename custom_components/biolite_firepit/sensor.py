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
    CCCD_DESCRIPTOR_UUID,
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

    async def async_update(self):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            return
        try:
            async with BleakClient(device, timeout=10.0) as client:
                if client.is_connected:
                    # Try reading standard Battery Level 0x2A19 first
                    val = None
                    try:
                        data = await client.read_gatt_char(BATTERY_LEVEL_CHARACTERISTIC_UUID)
                        if data and len(data) > 0:
                            val = int(data[0])
                    except Exception:
                        pass

                    # Fallback to BioLite Vendor Battery Percent characteristic
                    if val is None:
                        try:
                            data = await client.read_gatt_char(BATTERY_PERCENT_CHARACTERISTIC_UUID)
                            if data and len(data) > 0:
                                val = int(data[0])
                        except Exception:
                            pass

                    if val is not None:
                        self._attr_native_value = max(0, min(100, val))
                        _LOGGER.debug("Read battery level: %d%%", self._attr_native_value)
        except Exception as err:
            _LOGGER.debug("Error reading battery sensor: %s", err)

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

    async def async_update(self):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            return
        try:
            async with BleakClient(device, timeout=10.0) as client:
                if client.is_connected:
                    data = await client.read_gatt_char(TEMPERATURE_CHARACTERISTIC_UUID)
                    if data and len(data) > 0:
                        # Convert byte value as in MainActivity handleCharacteristicValue
                        raw_val = int(data[0])
                        f_temp = raw_val - 32
                        self._attr_native_value = f_temp
                        _LOGGER.debug("Read temperature: %d °F", f_temp)
        except Exception as err:
            _LOGGER.debug("Error reading temperature sensor: %s", err)
