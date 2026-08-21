"""Select platform for Panda Vent."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaVentCoordinator
from .entity import PandaVentEntity

LIGHT_MODES = ["Simple", "Advance", "Warning_Hot"]
SIMPLE_EFFECTS = ["Static", "Breathing", "Strobing", "Wave", "Marquee", "Color_Cycle", "Rainbow"]
SUB_EFFECTS = ["Static", "Strobing"]
LANGUAGES = ["en", "zh"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaVentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaVentLightModeSelect(coordinator),
        PandaVentSimpleEffectSelect(coordinator),
        PandaVentSafeEffectSelect(coordinator),
        PandaVentWarnEffectSelect(coordinator),
        PandaVentLanguageSelect(coordinator),
    ])


class PandaVentLightModeSelect(PandaVentEntity, SelectEntity):
    """Overall light mode: Simple, Advance (per-printer-state), or Warning_Hot."""

    _attr_name = "Light mode"
    _attr_icon = "mdi:led-strip-variant"
    _attr_options = LIGHT_MODES

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_light_mode_select"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("rgb_mode", {}).get("rgb_light_mode", 0)
        if 0 <= idx < len(LIGHT_MODES):
            return LIGHT_MODES[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/mode", {"mode": option})


class PandaVentSimpleEffectSelect(PandaVentEntity, SelectEntity):
    """Active effect while in Simple light mode."""

    _attr_name = "Simple effect"
    _attr_icon = "mdi:palette"
    _attr_options = SIMPLE_EFFECTS

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_simple_effect"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("rgb_mode", {}).get("current_simple_effect", 0)
        if 0 <= idx < len(SIMPLE_EFFECTS):
            return SIMPLE_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/simple/effect", {"effect": option})


class PandaVentSafeEffectSelect(PandaVentEntity, SelectEntity):
    """Sub-effect used below 50C in Warning_Hot mode."""

    _attr_name = "Safe temperature effect"
    _attr_icon = "mdi:thermometer-low"
    _attr_options = SUB_EFFECTS

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_safe_effect"

    @property
    def current_option(self) -> str | None:
        idx = (
            self.coordinator.data.get("rgb_mode", {})
            .get("warning_hot_mode", {})
            .get("safe", {})
            .get("current_effect", 0)
        )
        if 0 <= idx < len(SUB_EFFECTS):
            return SUB_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/warning-hot/safe-effect", {"effect": option})


class PandaVentWarnEffectSelect(PandaVentEntity, SelectEntity):
    """Sub-effect used above 50C in Warning_Hot mode."""

    _attr_name = "High temperature effect"
    _attr_icon = "mdi:thermometer-high"
    _attr_options = SUB_EFFECTS

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_warn_effect"

    @property
    def current_option(self) -> str | None:
        idx = (
            self.coordinator.data.get("rgb_mode", {})
            .get("warning_hot_mode", {})
            .get("warn", {})
            .get("current_effect", 0)
        )
        if 0 <= idx < len(SUB_EFFECTS):
            return SUB_EFFECTS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/light/warning-hot/warn-effect", {"effect": option})


class PandaVentLanguageSelect(PandaVentEntity, SelectEntity):
    """Device UI language."""

    _attr_name = "Language"
    _attr_icon = "mdi:translate"
    _attr_options = LANGUAGES

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_language"

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("settings", {}).get("language")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/language", {"language": option})
