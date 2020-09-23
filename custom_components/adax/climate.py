"""Support for Adax wifi-enabled home heaters."""
import logging

import voluptuous as vol


from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
)
from homeassistant.const import (
    CONF_PASSWORD,
    TEMP_CELSIUS,
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .adax import Adax

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required("account_id"): cv.string, vol.Required(CONF_PASSWORD): cv.string}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Adax thermostat."""
    account_id = config["account_id"]
    password = config[CONF_PASSWORD]

    adax_data_handler = Adax(
        account_id, password, websession=async_get_clientsession(hass)
    )

    dev = []
    for heater_data in await adax_data_handler.get_rooms():
        dev.append(AdaxDevice(heater_data, adax_data_handler))
    async_add_entities(dev)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Adax thermostat with config flow."""
    account_id = entry.data["account_id"]
    password = entry.data[CONF_PASSWORD]

    adax_data_handler = Adax(
        account_id, password, websession=async_get_clientsession(hass)
    )

    dev = []
    for heater_data in await adax_data_handler.get_rooms():
        dev.append(AdaxDevice(heater_data, adax_data_handler))
    async_add_entities(dev)


class AdaxDevice(ClimateEntity):
    """Representation of a heater."""

    def __init__(self, heater_data, adax_data_handler):
        """Initialize the heater."""
        self._heater_data = heater_data
        self._adax_data_handler = adax_data_handler

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._heater_data['homeId']}_{self._heater_data['id']}"

    @property
    def name(self):
        """Return the name of the device, if any."""
        return self._heater_data["name"]

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        if self._heater_data["heatingEnabled"]:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def icon(self):
        """Return nice icon for heater."""
        if self.hvac_mode == HVAC_MODE_HEAT:
            return "mdi:radiator"
        return "mdi:radiator-off"

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        if hvac_mode == HVAC_MODE_HEAT:
            temperature = max(
                self.min_temp, self._heater_data.get("targetTemperature", self.min_temp)
            )
            await self._adax_data_handler.set_room_target_temperature(
                self._heater_data["id"], temperature, True
            )
        elif hvac_mode == HVAC_MODE_OFF:
            await self._adax_data_handler.set_room_target_temperature(
                self._heater_data["id"], self.min_temp, False
            )
        else:
            return
        await self._adax_data_handler.update(force_update=True)

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this device uses."""
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 5

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 35

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._heater_data["temperature"]

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._heater_data["targetTemperature"]

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return PRECISION_WHOLE

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self._adax_data_handler.set_room_target_temperature(
            self._heater_data["id"], temperature, True
        )
        await self._adax_data_handler.update(force_update=True)

    async def async_update(self):
        """Get the latest data."""
        for room in await self._adax_data_handler.get_rooms():
            if room["id"] == self._heater_data["id"]:
                self._heater_data = room
                return
