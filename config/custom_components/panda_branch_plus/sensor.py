"""Sensor platform for Panda Branch Plus."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaBranchPlusCoordinator
from .entity import PandaBranchPlusEntity

PRINTER_STATES = {
    0: "Disconnected",
    1: "Connecting",
    2: "Connected",
    3: "Bound",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaBranchPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaBranchPlusFirmware(coordinator),
        PandaBranchPlusWifiSsid(coordinator),
        PandaBranchPlusIp(coordinator),
        PandaBranchPlusPrinterName(coordinator),
        PandaBranchPlusPrinterState(coordinator),
    ])


class PandaBranchPlusFirmware(PandaBranchPlusEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_firmware"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("settings", {}).get("fw_version", "Unknown")


class PandaBranchPlusWifiSsid(PandaBranchPlusEntity, SensorEntity):
    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_wifi_ssid"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("wifi", {}).get("ssid", "")


class PandaBranchPlusIp(PandaBranchPlusEntity, SensorEntity):
    _attr_name = "IP address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ip"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("sta", {}).get("ip", "")


class PandaBranchPlusPrinterName(PandaBranchPlusEntity, SensorEntity):
    _attr_name = "Printer"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_name"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("printer", {}).get("name", "")


class PandaBranchPlusPrinterState(PandaBranchPlusEntity, SensorEntity):
    _attr_name = "Printer state"
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(self, coordinator: PandaBranchPlusCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_state"

    @property
    def native_value(self) -> str:
        state = self.coordinator.data.get("printer", {}).get("state", 0)
        return PRINTER_STATES.get(state, f"Unknown ({state})")
