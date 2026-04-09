from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TibberVehicleSocApi, TibberVehicleSocApiError
from .const import (
    CONF_CAR_NAME,
    CONF_EMAIL,
    CONF_HOME_ID,
    CONF_PASSWORD,
    CONF_VEHICLE_ID,
    DOMAIN,
)


def _user_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_CAR_NAME, default=user_input.get(CONF_CAR_NAME, "")): str,
            vol.Required(CONF_EMAIL, default=user_input.get(CONF_EMAIL, "")): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_HOME_ID, default=user_input.get(CONF_HOME_ID, "")): str,
            vol.Required(CONF_VEHICLE_ID, default=user_input.get(CONF_VEHICLE_ID, "")): str,
        }
    )


class TibberVehicleSocUpdateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Tibber Vehicle SoC Update."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._async_validate_input(user_input)
            except TibberVehicleSocApiError:
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{user_input[CONF_HOME_ID]}:{user_input[CONF_VEHICLE_ID]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_CAR_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def _async_validate_input(self, user_input: dict[str, Any]) -> None:
        client = TibberVehicleSocApi(
            async_get_clientsession(self.hass),
            user_input[CONF_EMAIL],
            user_input[CONF_PASSWORD],
        )
        await client.async_validate_auth(user_input[CONF_HOME_ID])