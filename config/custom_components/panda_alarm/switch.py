"""Switch platform for Panda Alarm."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaAlarmCoordinator
from .entity import PandaAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaAlarmCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaAlarmSoundSwitch(coordinator),
    ])


class PandaAlarmSoundSwitch(PandaAlarmEntity, SwitchEntity):
    """Sound on/off switch."""

    _attr_name = "Sound"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_sound"

    @property
    def is_on(self) -> bool:
        # sound.on is read-only status on the device; on/off is driven by
        # volume (0 == muted). See panda-alarm-api /sound/toggle.
        return self.coordinator.data.get("sound", {}).get("volume", 0) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/sound/toggle", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post("/sound/toggle", {"on": False})
