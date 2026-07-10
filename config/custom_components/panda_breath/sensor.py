"""Sensor platform for Panda Breath."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaBreathCoordinator
from .entity import PandaBreathEntity

PRINTER_STATES = {
    0: "Disconnected",
    1: "Connecting",
    2: "Connected",
    3: "Bound",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaBreathCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaBreathFirmware(coordinator),
        PandaBreathWifiSsid(coordinator),
        PandaBreathIp(coordinator),
        PandaBreathPrinterName(coordinator),
        PandaBreathPrinterState(coordinator),
        PandaBreathRemainingTime(coordinator),
        PandaBreathChamberTemp(coordinator),
    ])


class PandaBreathFirmware(PandaBreathEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_firmware"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("settings", {}).get("fw_version", "Unknown")


class PandaBreathWifiSsid(PandaBreathEntity, SensorEntity):
    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_wifi_ssid"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("wifi", {}).get("ssid", "")


class PandaBreathIp(PandaBreathEntity, SensorEntity):
    _attr_name = "IP address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ip"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("sta", {}).get("ip", "")


class PandaBreathPrinterName(PandaBreathEntity, SensorEntity):
    _attr_name = "Printer"
    _attr_icon = "mdi:printer-3d"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_name"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("printer", {}).get("name", "")


class PandaBreathPrinterState(PandaBreathEntity, SensorEntity):
    _attr_name = "Printer state"
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_printer_state"

    @property
    def native_value(self) -> str:
        state = self.coordinator.data.get("printer", {}).get("state", 0)
        return PRINTER_STATES.get(state, f"Unknown ({state})")


class PandaBreathRemainingTime(PandaBreathEntity, SensorEntity):
    _attr_name = "Remaining time"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_remaining_time"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.get("settings", {}).get("remaining_seconds", 0)


class PandaBreathChamberTemp(PandaBreathEntity, SensorEntity):
    _attr_name = "Chamber temperature"
    _attr_icon = "mdi:thermometer"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "\u00b0C"

    def __init__(self, coordinator: PandaBreathCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_chamber_temp"

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data.get("settings", {}).get("warehouse_temper")
        if val is not None:
            return float(val)
        return None
