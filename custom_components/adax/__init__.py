"""The Adax heater integration."""
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)


async def async_setup(hass, config):
    """Set up the Adax platform."""
    return True

async def async_setup_entry(hass, entry):
    """Set up the Adax heater."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        config_entry, "climate"
    )
    return unload_ok

