"""Adds config flow for Adax integration."""
import logging

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .adax import get_adax_token
from .const import ACCOUNT_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {vol.Required(ACCOUNT_ID): int, vol.Required(CONF_PASSWORD): str}
)


async def validate_input(hass: core.HomeAssistant, account_id, password):
    """Validate the user input allows us to connect."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data[ACCOUNT_ID] == account_id:
            raise AlreadyConfigured

    token = await get_adax_token(async_get_clientsession(hass), account_id, password)
    if token is None:
        _LOGGER.info("Adax: Failed to login to retrieve token")
        raise CannotConnect


class AdaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Adax integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                account_id = user_input[ACCOUNT_ID]
                password = user_input[CONF_PASSWORD].replace(" ", "")
                await validate_input(self.hass, account_id, password)
                unique_id = account_id
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=unique_id,
                    data={ACCOUNT_ID: account_id, CONF_PASSWORD: password},
                )

            except AlreadyConfigured:
                return self.async_abort(reason="already_configured")
            except CannotConnect:
                errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate host is already configured."""
