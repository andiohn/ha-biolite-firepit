import logging
import math
from typing import Any, Optional
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak import BleakClient

from .const import (
    DOMAIN,
    FAN_SPEED_CHARACTERISTIC_UUID,
    FAN_SPEED_OFF,
    PRESET_OFF,
    PRESET_LOW,
    PRESET_MEDIUM,
    PRESET_HIGH,
    PRESET_MAX,
    PRESET_TO_SPEED,
    SPEED_TO_PRESET,
    SPEED_TO_PERCENTAGE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([BioLiteFirePitFan(hass, mac)])

class BioLiteFirePitFan(FanEntity):
    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_supported_features = (
        FanEntityFeature.PRESET_MODE
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    def __init__(self, hass, mac):
        self.hass = hass
        self._mac = mac
        self._attr_unique_id = f"{mac}_fan"
        self._attr_preset_modes = [PRESET_OFF, PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH, PRESET_MAX]
        self._attr_preset_mode = PRESET_OFF
        self._attr_percentage = 0
        self._attr_is_on = False

    @property
    def percentage_step(self) -> float:
        """Step size for speed percentage slider (4 speeds above off = 25% steps)."""
        return 25.0

    @property
    def speed_count(self) -> int:
        """Number of discrete speeds above off."""
        return 4

    async def _write_fan_speed(self, speed_val: int):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            _LOGGER.error("BioLite FirePit BLE device not found for address %s", self._mac)
            return
        async with BleakClient(device) as client:
            await client.write_gatt_char(FAN_SPEED_CHARACTERISTIC_UUID, bytes([speed_val]))

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed using percentage slider (0-100%)."""
        if percentage == 0:
            speed_val = FAN_SPEED_OFF
        else:
            speed_val = min(4, max(1, math.ceil(percentage / 25.0)))

        await self._write_fan_speed(speed_val)
        self._attr_percentage = SPEED_TO_PERCENTAGE[speed_val]
        self._attr_preset_mode = SPEED_TO_PRESET[speed_val]
        self._attr_is_on = (speed_val != FAN_SPEED_OFF)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set fan speed using preset mode dropdown or buttons."""
        if preset_mode in PRESET_TO_SPEED:
            speed_val = PRESET_TO_SPEED[preset_mode]
            await self._write_fan_speed(speed_val)
            self._attr_percentage = SPEED_TO_PERCENTAGE[speed_val]
            self._attr_preset_mode = preset_mode
            self._attr_is_on = (speed_val != FAN_SPEED_OFF)
            self.async_write_ha_state()

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        """Turn on fan."""
        if percentage is not None:
            await self.async_set_percentage(percentage)
        elif preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        else:
            await self.async_set_preset_mode(PRESET_LOW)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off fan."""
        await self.async_set_percentage(0)
