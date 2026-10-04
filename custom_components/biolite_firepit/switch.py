import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak import BleakClient

from .const import DOMAIN, CHARGING_STATUS_CHARACTERISTIC_UUID

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([BioLiteUsbChargerSwitch(hass, mac)])

class BioLiteUsbChargerSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "USB Charger"

    def __init__(self, hass, mac):
        self.hass = hass
        self._mac = mac
        self._attr_unique_id = f"{mac}_usb_charger"
        self._attr_is_on = False

    async def _write_charger_state(self, state: bool):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            _LOGGER.error("BioLite FirePit BLE device not found for address %s", self._mac)
            return
        val = 1 if state else 0
        async with BleakClient(device) as client:
            await client.write_gatt_char(CHARGING_STATUS_CHARACTERISTIC_UUID, bytes([val]))

    async def async_turn_on(self, **kwargs):
        await self._write_charger_state(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._write_charger_state(False)
        self._attr_is_on = False
        self.async_write_ha_state()
