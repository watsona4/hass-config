"""Sensor platform for Panda Vent."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaVentCoordinator
from .entity import PandaVentEntity

PRINTER_STATES = {
    0: "Unbound",
    1: "Unbound",
    2: "Binding",
    3: "Bound",
    4: "IP error",
    5: "Serial number error",
    6: "Access code error",
    7: "Unknown error",
}

LIGHT_MODES = ["Simple", "Advance", "Warning Hot"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaVentCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaVentFirmware(coordinator),
        PandaVentWifiSsid(coordinator),
        PandaVentIp(coordinator),
        PandaVentPrinterName(coordinator),
        PandaVentPrinterState(coordinator),
        PandaVentLightMode(coordinator),
    ])


class PandaVentFirmware(PandaVentEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_firmware"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("settings", {}).get("fw_version", "Unknown")


class PandaVentWifiSsid(PandaVentEntity, SensorEntity):
    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_wifi_ssid"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("wifi", {}).get("ssid", "")


class PandaVentIp(PandaVentEntity, SensorEntity):
    _attr_name = "IP address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ip"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("sta", {}).get("ip", "")


class PandaVentPrinterName(PandaVentEntity, SensorEntity):
    _attr_name = "Printer"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_name"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("printer", {}).get("name", "")


class PandaVentPrinterState(PandaVentEntity, SensorEntity):
    _attr_name = "Printer state"
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_state"

    @property
    def native_value(self) -> str:
        state = self.coordinator.data.get("printer", {}).get("state", 0)
        return PRINTER_STATES.get(state, f"Unknown ({state})")


class PandaVentLightMode(PandaVentEntity, SensorEntity):
    """Overall light mode: Simple, Advance (per-printer-state), or Warning Hot."""

    _attr_name = "Light mode"
    _attr_icon = "mdi:led-strip-variant"

    def __init__(self, coordinator: PandaVentCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_light_mode"

    @property
    def native_value(self) -> str:
        idx = self.coordinator.data.get("rgb_mode", {}).get("rgb_light_mode", 0)
        if 0 <= idx < len(LIGHT_MODES):
            return LIGHT_MODES[idx]
        return f"Unknown ({idx})"
