"""Select platform for Panda Alarm."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaAlarmCoordinator
from .entity import PandaAlarmEntity

SOUND_EFFECTS = ["Pulse", "Prompt", "Beep", "Silent", "Custom"]
PREVIEW_STATUSES = {
    1: "OTA",
    2: "No MQTT",
    3: "Binding",
    4: "Idle",
    5: "Printing",
    6: "Pause",
    7: "Done",
    8: "Alarm",
    9: "Prepare",
    10: "Downloading",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaAlarmCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaAlarmSoundEffectDone(coordinator),
        PandaAlarmSoundEffectAlarm(coordinator),
        PandaAlarmPreviewStatus(coordinator),
    ])


class PandaAlarmSoundEffectDone(PandaAlarmEntity, SelectEntity):
    """Sound effect for print done."""

    _attr_name = "Sound effect (done)"
    _attr_icon = "mdi:bell-ring"
    _attr_options = SOUND_EFFECTS

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_sound_effect_done"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("sound", {}).get("effect", {}).get("done", 0)
        if 0 <= idx < len(SOUND_EFFECTS):
            return SOUND_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        idx = SOUND_EFFECTS.index(option)
        await self.coordinator.api_post("/sound/effect", {"done": idx})


class PandaAlarmSoundEffectAlarm(PandaAlarmEntity, SelectEntity):
    """Sound effect for alarm."""

    _attr_name = "Sound effect (alarm)"
    _attr_icon = "mdi:alarm-light"
    _attr_options = SOUND_EFFECTS

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_sound_effect_alarm"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("sound", {}).get("effect", {}).get("alarm", 0)
        if 0 <= idx < len(SOUND_EFFECTS):
            return SOUND_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        idx = SOUND_EFFECTS.index(option)
        await self.coordinator.api_post("/sound/effect", {"alarm": idx})


class PandaAlarmPreviewStatus(PandaAlarmEntity, SelectEntity):
    """Preview mode simulated status."""

    _attr_name = "Preview status"
    _attr_icon = "mdi:eye-settings"
    _attr_options = list(PREVIEW_STATUSES.values())

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_preview_status"

    @property
    def current_option(self) -> str | None:
        status = self.coordinator.data.get("preview", {}).get("status", 1)
        return PREVIEW_STATUSES.get(status)

    async def async_select_option(self, option: str) -> None:
        for k, v in PREVIEW_STATUSES.items():
            if v == option:
                await self.coordinator.api_post("/preview/status", {"status": k})
                return
