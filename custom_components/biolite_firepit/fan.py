import logging
import math
from typing import Any, Optional
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.util.percentage import (
    ranged_value_to_percentage,
    percentage_to_ranged_value,
)
from bleak import BleakClient

from .const import (
    DOMAIN,
    FAN_SPEED_CHARACTERISTIC_UUID,
    CCCD_DESCRIPTOR_UUID,
    PRESET_OFF,
    PRESET_LOW,
    PRESET_MED,
    PRESET_HIGH,
    PRESET_ON,
    PRESET_TO_SPEED,
    SPEED_TO_PRESET,
)

_LOGGER = logging.getLogger(__name__)

SPEED_RANGE = (1, 4)  # 1=Low, 2=Med, 3=High, 4=On/Max

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
        self._attr_preset_modes = [PRESET_OFF, PRESET_LOW, PRESET_MED, PRESET_HIGH, PRESET_ON]
        self._attr_preset_mode = PRESET_OFF
        self._attr_percentage = 0
        self._attr_is_on = False

    async def _write_fan_speed(self, speed_val: int):
        device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not device:
            _LOGGER.error("BioLite FirePit BLE device not found for address %s", self._mac)
            return
        try:
            async with BleakClient(device, timeout=15.0) as client:
                if client.is_connected:
                    # Enable BLE CCCD Notification descriptor routine as performed in MainActivity.java
                    try:
                        char = client.services.get_characteristic(FAN_SPEED_CHARACTERISTIC_UUID)
                        if char:
                            desc = char.get_descriptor(CCCD_DESCRIPTOR_UUID)
                            if desc:
                                await client.write_descriptor(desc, bytes([0x01, 0x00]))
                    except Exception as desc_err:
                        _LOGGER.debug("CCCD descriptor write skipped/not required: %s", desc_err)

                    await client.write_gatt_char(FAN_SPEED_CHARACTERISTIC_UUID, bytes([speed_val]), response=True)
                    _LOGGER.info("Successfully wrote fan speed %d to BioLite FirePit", speed_val)
        except Exception as err:
            _LOGGER.error("Failed to write fan speed to BioLite FirePit: %s", err)

    @property
    def speed_count(self) -> int:
        return 4  # Low, Med, High, On

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            await self.async_set_preset_mode(PRESET_LOW)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write_fan_speed(0)
        self._attr_preset_mode = PRESET_OFF
        self._attr_percentage = 0
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return

        # Map percentage 1..100 to speed values 1..4
        speed_val = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        speed_val = max(1, min(4, speed_val))
        
        await self._write_fan_speed(speed_val)
        self._attr_percentage = ranged_value_to_percentage(SPEED_RANGE, speed_val)
        self._attr_preset_mode = SPEED_TO_PRESET.get(speed_val, PRESET_LOW)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode in PRESET_TO_SPEED:
            speed_val = PRESET_TO_SPEED[preset_mode]
            await self._write_fan_speed(speed_val)
            self._attr_preset_mode = preset_mode
            if speed_val == 0:
                self._attr_percentage = 0
                self._attr_is_on = False
            else:
                self._attr_percentage = ranged_value_to_percentage(SPEED_RANGE, speed_val)
                self._attr_is_on = True
            self.async_write_ha_state()

async def async_setup_entry(hass, entry, async_add_entities):
    mac = entry.data["mac"]
    async_add_entities([BioLiteFirePitFan(hass, mac)])
