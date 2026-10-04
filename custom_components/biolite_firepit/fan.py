import logging
from typing import Any, Optional
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak import BleakClient

from .const import (
    DOMAIN,
    FAN_SPEED_CHARACTERISTIC_UUID,
    PRESET_OFF,
    PRESET_LOW,
    PRESET_MEDIUM,
    PRESET_HIGH,
    PRESET_MAX,
    PRESET_TO_SPEED,
    SPEED_TO_PRESET,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([BioLiteFirePitFan(hass, mac)])

class BioLiteFirePitFan(FanEntity):
    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_supported_features = FanEntityFeature.PRESET_MODE | FanEntityFeature.SET_SPEED

    def __init__(self, hass, mac):
        self.hass = hass
        self._mac = mac
        self._attr_unique_id = f"{mac}_fan"
        self._attr_preset_modes = [PRESET_OFF, PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH, PRESET_MAX]
        self._attr_preset_mode = PRESET_OFF
        self._attr_is_on = False

    async def _write_fan_speed(self, speed_val: int):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            _LOGGER.error("BioLite FirePit BLE device not found for address %s", self._mac)
            return
        async with BleakClient(device) as client:
            await client.write_gatt_char(FAN_SPEED_CHARACTERISTIC_UUID, bytes([speed_val]))

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        target_preset = preset_mode or PRESET_LOW
        await self.async_set_preset_mode(target_preset)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_set_preset_mode(PRESET_OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode in PRESET_TO_SPEED:
            speed_val = PRESET_TO_SPEED[preset_mode]
            await self._write_fan_speed(speed_val)
            self._attr_preset_mode = preset_mode
            self._attr_is_on = (preset_mode != PRESET_OFF)
            self.async_write_ha_state()
