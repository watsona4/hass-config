"""DataUpdateCoordinator for Panda Vent."""

from __future__ import annotations

from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER


class PandaVentCoordinator(DataUpdateCoordinator):
    """Panda Vent data update coordinator."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self._host = host
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._host}/state",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return await resp.json()
        except Exception as exc:
            raise UpdateFailed(f"Error communicating with Panda Vent API: {exc}") from exc

    async def api_post(self, path: str, json: dict | None = None) -> dict:
        """Send a POST command to the API."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._host}{path}",
                json=json or {},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                result = await resp.json()
        await self.async_request_refresh()
        return result
