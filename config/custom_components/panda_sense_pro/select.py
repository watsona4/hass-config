"""Select platform for Panda Sense Pro."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaSenseProCoordinator
from .entity import PandaSenseProEntity

LANGUAGES = ["en", "zh"]
TEMP_UNITS = ["C", "F"]
SCREENSAVER_MODES = ["Reduce_Brightness", "Character_Rain", "Collision_Balls", "Clock", "GIF"]
CLOCK_TYPES = ["Roll", "Flip"]

TIMEOUT_OPTIONS = {0: "Off", 1: "1 min", 5: "5 min", 10: "10 min", 30: "30 min", 60: "60 min"}
SLEEP_DELAY_OPTIONS = {
    0: "Off", 1: "1 min", 5: "5 min", 10: "10 min",
    30: "30 min", 60: "60 min", 99: "Never",
}
SCREENSAVER_BRIGHTNESS_OPTIONS = {10: "10%", 20: "20%", 30: "30%", 40: "40%", 50: "50%", 60: "60%"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaSenseProCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaSenseProLanguageSelect(coordinator),
        PandaSenseProTempUnitSelect(coordinator),
        PandaSenseProScreensaverModeSelect(coordinator),
        PandaSenseProClockTypeSelect(coordinator),
        PandaSenseProScreensaverTimeoutSelect(coordinator),
        PandaSenseProSleepDelaySelect(coordinator),
        PandaSenseProScreensaverBrightnessSelect(coordinator),
    ])


class PandaSenseProLanguageSelect(PandaSenseProEntity, SelectEntity):
    _attr_name = "Language"
    _attr_icon = "mdi:translate"
    _attr_options = LANGUAGES

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_language"

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("settings", {}).get("language")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/language", {"language": option})


class PandaSenseProTempUnitSelect(PandaSenseProEntity, SelectEntity):
    _attr_name = "Temperature unit"
    _attr_icon = "mdi:thermometer"
    _attr_options = TEMP_UNITS

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_temp_unit"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("temp_unit", 0)
        if 0 <= idx < len(TEMP_UNITS):
            return TEMP_UNITS[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/temp-unit", {"unit": option})


class PandaSenseProScreensaverModeSelect(PandaSenseProEntity, SelectEntity):
    _attr_name = "Screensaver mode"
    _attr_icon = "mdi:monitor-screenshot"
    _attr_options = SCREENSAVER_MODES

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_screensaver_mode"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("screensaver_mode", 0)
        if 0 <= idx < len(SCREENSAVER_MODES):
            return SCREENSAVER_MODES[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/screensaver-mode", {"mode": option})


class PandaSenseProClockTypeSelect(PandaSenseProEntity, SelectEntity):
    """Only relevant when screensaver mode is Clock."""

    _attr_name = "Screensaver clock type"
    _attr_icon = "mdi:clock-outline"
    _attr_options = CLOCK_TYPES

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_screensaver_clock_type"

    @property
    def current_option(self) -> str | None:
        idx = self.coordinator.data.get("settings", {}).get("screensaver_clock_type", 0)
        if 0 <= idx < len(CLOCK_TYPES):
            return CLOCK_TYPES[idx]
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api_post("/settings/screensaver-clock-type", {"clock_type": option})


class PandaSenseProScreensaverTimeoutSelect(PandaSenseProEntity, SelectEntity):
    """How long the screen must be idle before the screensaver starts."""

    _attr_name = "Screensaver timeout"
    _attr_icon = "mdi:timer-outline"
    _attr_options = list(TIMEOUT_OPTIONS.values())

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_screensaver_timeout"

    @property
    def current_option(self) -> str | None:
        minutes = self.coordinator.data.get("settings", {}).get("screensaver_timeout", 0)
        return TIMEOUT_OPTIONS.get(minutes)

    async def async_select_option(self, option: str) -> None:
        for minutes, label in TIMEOUT_OPTIONS.items():
            if label == option:
                await self.coordinator.api_post("/settings/screensaver-timeout", {"minutes": minutes})
                return


class PandaSenseProSleepDelaySelect(PandaSenseProEntity, SelectEntity):
    """How long after the screensaver starts before the screen fully sleeps."""

    _attr_name = "Sleep trigger delay"
    _attr_icon = "mdi:sleep"
    _attr_options = list(SLEEP_DELAY_OPTIONS.values())

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_sleep_delay"

    @property
    def current_option(self) -> str | None:
        minutes = self.coordinator.data.get("settings", {}).get("screensaver_sleep_delay", 0)
        return SLEEP_DELAY_OPTIONS.get(minutes)

    async def async_select_option(self, option: str) -> None:
        for minutes, label in SLEEP_DELAY_OPTIONS.items():
            if label == option:
                await self.coordinator.api_post("/settings/sleep-delay", {"minutes": minutes})
                return


class PandaSenseProScreensaverBrightnessSelect(PandaSenseProEntity, SelectEntity):
    _attr_name = "Screensaver brightness"
    _attr_icon = "mdi:brightness-4"
    _attr_options = list(SCREENSAVER_BRIGHTNESS_OPTIONS.values())

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_screensaver_brightness"

    @property
    def current_option(self) -> str | None:
        pct = self.coordinator.data.get("settings", {}).get("screensaver_brightness", 10)
        return SCREENSAVER_BRIGHTNESS_OPTIONS.get(pct)

    async def async_select_option(self, option: str) -> None:
        for pct, label in SCREENSAVER_BRIGHTNESS_OPTIONS.items():
            if label == option:
                await self.coordinator.api_post("/settings/screensaver-brightness", {"brightness": pct})
                return
