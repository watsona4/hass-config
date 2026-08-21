"""Sensor platform for Panda Sense Pro."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaSenseProCoordinator
from .entity import PandaSenseProEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaSenseProCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PandaSenseProPm25(coordinator),
        PandaSenseProPm10(coordinator),
        PandaSenseProTemperature(coordinator),
        PandaSenseProHumidity(coordinator),
        PandaSenseProTvoc(coordinator),
        PandaSenseProCo2(coordinator),
        PandaSenseProAqi(coordinator),
        PandaSenseProFormaldehyde(coordinator),
        PandaSenseProFirmware(coordinator),
        PandaSenseProWifiSsid(coordinator),
        PandaSenseProIp(coordinator),
    ])


class PandaSenseProPm25(PandaSenseProEntity, SensorEntity):
    _attr_name = "PM2.5"
    _attr_device_class = SensorDeviceClass.PM25
    _attr_native_unit_of_measurement = "µg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_pm2_5"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("pm2_5")


class PandaSenseProPm10(PandaSenseProEntity, SensorEntity):
    _attr_name = "PM10"
    _attr_device_class = SensorDeviceClass.PM10
    _attr_native_unit_of_measurement = "µg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_pm10"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("pm10")


class PandaSenseProTemperature(PandaSenseProEntity, SensorEntity):
    _attr_name = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_temperature"

    @property
    def native_unit_of_measurement(self) -> str:
        # settings.temp_unit: 0=C, 1=F -- the device's `device.temp` value is
        # already expressed in this unit.
        unit = self.coordinator.data.get("settings", {}).get("temp_unit", 0)
        return "°F" if unit == 1 else "°C"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("temp")


class PandaSenseProHumidity(PandaSenseProEntity, SensorEntity):
    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_humidity"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("humidity")


class PandaSenseProTvoc(PandaSenseProEntity, SensorEntity):
    """eTVOC (total volatile organic compounds)."""

    _attr_name = "TVOC"
    _attr_device_class = SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
    _attr_native_unit_of_measurement = "mg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT
#    _attr_icon = "mdi:molecule"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_tvoc"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("tvoc")


class PandaSenseProCo2(PandaSenseProEntity, SensorEntity):
    _attr_name = "CO2"
    _attr_device_class = SensorDeviceClass.CO2
    _attr_native_unit_of_measurement = "ppm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_co2"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("co2")


class PandaSenseProAqi(PandaSenseProEntity, SensorEntity):
    _attr_name = "AQI"
    _attr_device_class = SensorDeviceClass.AQI
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_aqi"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("aqi")


class PandaSenseProFormaldehyde(PandaSenseProEntity, SensorEntity):
    _attr_name = "Formaldehyde"
    _attr_native_unit_of_measurement = "mg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ch2o"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("device", {}).get("ch2o")


class PandaSenseProFirmware(PandaSenseProEntity, SensorEntity):
    _attr_name = "Firmware"
    _attr_icon = "mdi:chip"
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_firmware"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("settings", {}).get("fw_version", "Unknown")


class PandaSenseProWifiSsid(PandaSenseProEntity, SensorEntity):
    _attr_name = "WiFi SSID"
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_wifi_ssid"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("wifi", {}).get("ssid", "")


class PandaSenseProIp(PandaSenseProEntity, SensorEntity):
    _attr_name = "IP address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: PandaSenseProCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator._host}_ip"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("sta", {}).get("ip", "")
