"""Switch platform for Panda Branch Plus."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PandaBranchPlusCoordinator
from .entity import PandaBranchPlusEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PandaBranchPlusCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []
    for outlet_id in range(1, 6):
        entities.append(PandaBranchPlusOutletSwitch(coordinator, "usb", outlet_id))
        entities.append(PandaBranchPlusOutletSwitch(coordinator, "mx24v", outlet_id))
    async_add_entities(entities)


class PandaBranchPlusOutletSwitch(PandaBranchPlusEntity, SwitchEntity):
    """USB or MX24V power outlet switch."""

    _attr_icon = "mdi:power-socket-us"

    def __init__(self, coordinator: PandaBranchPlusCoordinator, group: str, outlet_id: int) -> None:
        super().__init__(coordinator)
        self._group = group
        self._outlet_id = outlet_id
        label = "USB" if group == "usb" else "MX24V"
        self._attr_name = f"{label} {outlet_id}"
        self._attr_unique_id = f"{coordinator._host}_{group}_{outlet_id}"

    @property
    def is_on(self) -> bool:
        for item in self.coordinator.data.get("control", {}).get(self._group, []):
            if item.get("id") == self._outlet_id:
                return bool(item.get("on"))
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api_post(f"/control/{self._group}/{self._outlet_id}/toggle", {"on": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api_post(f"/control/{self._group}/{self._outlet_id}/toggle", {"on": False})
