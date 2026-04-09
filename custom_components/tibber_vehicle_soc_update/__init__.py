from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TibberVehicleSocApi, TibberVehicleSocApiError
from .const import (
    CONF_CAR_NAME,
    CONF_CONFIG_ENTRY_ID,
    CONF_CURRENT_SOC,
    CONF_EMAIL,
    CONF_HOME_ID,
    CONF_PASSWORD,
    CONF_SOC,
    CONF_VEHICLE_ID,
    DEFAULT_CURRENT_SOC,
    DOMAIN,
    SERVICE_SET_SOC,
)

PLATFORMS: list[Platform] = []
LOGGER = logging.getLogger(__name__)


@dataclass
class TibberRuntimeData:
    """Runtime data for a configured Tibber vehicle entry."""

    api: TibberVehicleSocApi
    lock: asyncio.Lock


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    _async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Tibber vehicle SoC config entry."""
    api = TibberVehicleSocApi(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    try:
        await api.async_validate_auth(entry.data[CONF_HOME_ID])
    except TibberVehicleSocApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    runtime_data = TibberRuntimeData(api=api, lock=asyncio.Lock())
    hass.data[DOMAIN][entry.entry_id] = runtime_data
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Tibber vehicle SoC config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)

    return True


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SET_SOC):
        return

    async def async_handle_set_soc(call: ServiceCall) -> None:
        entry = _async_resolve_entry(hass, call.data[CONF_CONFIG_ENTRY_ID])
        try:
            await _async_apply_soc(hass, entry, call.data[CONF_SOC], source="service")
        except TibberVehicleSocApiError as err:
            raise ServiceValidationError(
                f"Unable to update Tibber vehicle SoC: {err}"
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SOC,
        async_handle_set_soc,
        schema=vol.Schema(
            {
                vol.Required(CONF_CONFIG_ENTRY_ID): str,
                vol.Required(CONF_SOC): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            }
        ),
    )


async def _async_apply_soc(
    hass: HomeAssistant, entry: ConfigEntry, soc: int, source: str
) -> None:
    runtime_data: TibberRuntimeData = hass.data[DOMAIN][entry.entry_id]

    async with runtime_data.lock:
        await runtime_data.api.async_set_vehicle_soc(
            entry.data[CONF_HOME_ID],
            entry.data[CONF_VEHICLE_ID],
            soc,
        )

        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_CURRENT_SOC: soc,
            },
        )

        LOGGER.info(
            "Updated Tibber vehicle %s SoC to %s%% via %s",
            entry.data.get(CONF_CAR_NAME, entry.data[CONF_VEHICLE_ID]),
            soc,
            source,
        )


def _async_resolve_entry(hass: HomeAssistant, entry_id: str) -> ConfigEntry:
    if entry_id not in hass.data[DOMAIN]:
        raise ServiceValidationError(f"Unknown or unloaded config entry: {entry_id}")

    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(f"Unknown config entry: {entry_id}")

    return entry