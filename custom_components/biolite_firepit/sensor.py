import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([BioLiteBatterySensor(hass, mac)])

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
