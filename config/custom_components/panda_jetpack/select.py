"""Select platform for Panda Jetpack."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaJetpackCoordinator
from .entity import PandaJetpackEntity

RGB_EFFECTS = [
    "Static", "Breathing", "Strobing", "Wave", "Marquee",
    "Color_Cycle", "Rainbow", "Warning_Hot", "Fan_Speed", "H2D",
]
SUB_EFFECTS = ["Static", "Strobing"]
LANGUAGES = ["en", "zh"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaJetpackCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaJetpackLightEffectSelect(coordinator),
        PandaJetpackSafeEffectSelect(coordinator),
        PandaJetpackDangerEffectSelect(coordinator),
        PandaJetpackLanguageSelect(coordinator),
    ])


class PandaJetpackLightEffectSelect(PandaJetpackEntity, SelectEntity):
    """Active light-effect mode."""

    _attr_name = "Light effect"
    _attr_icon = "mdi:led-strip-variant"
    _attr_options = RGB_EFFECTS

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_light_effect_select"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("current_mode", 0)
        if 0 <= idx < len(RGB_EFFECTS):
            return RGB_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/mode", {"effect": option})


class PandaJetpackSafeEffectSelect(PandaJetpackEntity, SelectEntity):
    """Sub-effect used below 50C in Warning_Hot mode."""

    _attr_name = "Safe temperature effect"
    _attr_icon = "mdi:thermometer-low"
    _attr_options = SUB_EFFECTS

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_safe_effect"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("safe_current_mode", 0)
        if 0 <= idx < len(SUB_EFFECTS):
            return SUB_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/safe-effect", {"effect": option})


class PandaJetpackDangerEffectSelect(PandaJetpackEntity, SelectEntity):
    """Sub-effect used above 50C in Warning_Hot mode."""

    _attr_name = "Danger temperature effect"
    _attr_icon = "mdi:thermometer-high"
    _attr_options = SUB_EFFECTS

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_danger_effect"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("danger_current_mode", 0)
        if 0 <= idx < len(SUB_EFFECTS):
            return SUB_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/danger-effect", {"effect": option})


class PandaJetpackLanguageSelect(PandaJetpackEntity, SelectEntity):
    """Device UI language."""

    _attr_name = "Language"
    _attr_icon = "mdi:translate"
    _attr_options = LANGUAGES

    def __init__(self, coordinator: PandaJetpackCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_language"

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("settings", {}).get("language")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/language", {"language": option})
