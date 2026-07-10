"""Sensor platform for Panda Alarm."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaAlarmCoordinator
from .entity import PandaAlarmEntity

PRINTER_STATES = {
    0: "Disconnected",
    1: "Connecting",
    2: "Connected",
    3: "Bound",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaAlarmCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaAlarmFirmware(coordinator),
        PandaAlarmWifiSsid(coordinator),
        PandaAlarmIp(coordinator),
        PandaAlarmPrinterName(coordinator),
        PandaAlarmPrinterState(coordinator),
        PandaAlarmLedColorIdle(coordinator),
        PandaAlarmLedColorPrinting(coordinator),
        PandaAlarmLedColorAlarm(coordinator),
    ])


class PandaAlarmFirmware(PandaAlarmEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_firmware"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("settings", {}).get("fw_version", "Unknown")


class PandaAlarmWifiSsid(PandaAlarmEntity, SensorEntity):
    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_wifi_ssid"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("wifi", {}).get("ssid", "")


class PandaAlarmIp(PandaAlarmEntity, SensorEntity):
    _attr_name = "IP address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ip"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("sta", {}).get("ip", "")


class PandaAlarmPrinterName(PandaAlarmEntity, SensorEntity):
    _attr_name = "Printer"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_name"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("printer", {}).get("name", "")


class PandaAlarmPrinterState(PandaAlarmEntity, SensorEntity):
    _attr_name = "Printer state"
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_state"

    @property
    def native_value(self) -> str:
        state = self.coordinator.data.get("printer", {}).get("state", 0)
        return PRINTER_STATES.get(state, f"Unknown ({state})")


class PandaAlarmLedColorIdle(PandaAlarmEntity, SensorEntity):
    _attr_name = "LED color (idle)"
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_led_color_idle"

    @property
    def native_value(self) -> str:
        return "#" + self.coordinator.data.get("led", {}).get("rgb", {}).get("idle", "FFFFFF")


class PandaAlarmLedColorPrinting(PandaAlarmEntity, SensorEntity):
    _attr_name = "LED color (printing)"
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_led_color_printing"

    @property
    def native_value(self) -> str:
        return "#" + self.coordinator.data.get("led", {}).get("rgb", {}).get("printing", "0000FF")


class PandaAlarmLedColorAlarm(PandaAlarmEntity, SensorEntity):
    _attr_name = "LED color (alarm)"
    _attr_icon = "mdi:palette"

    def __init__(self, coordinator: PandaAlarmCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_led_color_alarm"

    @property
    def native_value(self) -> str:
        return "#" + self.coordinator.data.get("led", {}).get("rgb", {}).get("alarm", "FF0000")
