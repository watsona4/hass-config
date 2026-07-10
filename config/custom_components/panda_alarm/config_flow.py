"""Config flow for Panda Alarm."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_HOST, DOMAIN, LOGGER


class PandaAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Panda Alarm."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].rstrip("/")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{host}/health", timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        data = await resp.json()
                        LOGGER.info("Panda Alarm health response: %s", data)
                        if data.get("status") != "ok":
                            errors["base"] = "cannot_connect"
            except Exception as exc:
                LOGGER.error("Panda Alarm config flow error: %s", exc)
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(f"panda_alarm_{host}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Panda Alarm", data={CONF_HOST: host}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST, default="http://localhost:8060"): str}
            ),
            errors=errors,
        )
