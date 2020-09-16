"""Adds config flow for Mill integration."""
import logging

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

API_URL = "https://api-1.adax.no/client-api"

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str}
)


class AdaxConfigFlow(config_entries.ConfigFlow, domain="adax"):
    """Handle a config flow for Mill integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors={},
            )

        username = user_input[CONF_USERNAME].replace(" ", "")
        password = user_input[CONF_PASSWORD].replace(" ", "")

        """
        TEST LOGIN
        """
        data = {'username': username,
            'password': password,
            'grant_type': 'password'}

        ACCESS_TOKEN_URL = API_URL + '/auth/token'

        async with aiohttp.ClientSession() as session:
            async with session.post(ACCESS_TOKEN_URL, data=data) as response:
                errors = {}
                if response.status != 200:
                    _LOGGER.info("Adax: Failed to login to retrieve token: %d", response.status)
                    errors["connection_error"] = "connection_error"
                    return self.async_show_form(
                        step_id="user", data_schema=DATA_SCHEMA, errors=errors,
                    )

        _LOGGER.info("Adax: Login succesful. Config entry created.")

        unique_id = username

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=unique_id, data={CONF_USERNAME: username, CONF_PASSWORD: password},
        )
