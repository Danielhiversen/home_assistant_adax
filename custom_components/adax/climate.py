"""Support for Adax wifi-enabled home heaters."""
import asyncio
import datetime
import json
import logging

import aiohttp
import async_timeout
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

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required("account_id"): cv.string, vol.Required(CONF_PASSWORD): cv.string}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Adax thermostat."""
    client_id = config["account_id"]
    client_secret = config[CONF_PASSWORD]

    adax_data_handler = Adax(
        client_id, client_secret, websession=async_get_clientsession(hass)
    )

    dev = []
    for heater_data in await adax_data_handler.get_rooms():
        dev.append(AdaxDevice(heater_data, adax_data_handler))
    async_add_entities(dev)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Adax thermostat with config flow"""
    client_id = entry.data["account_id"]
    client_secret = entry.data[CONF_PASSWORD]

    adax_data_handler = Adax(
        client_id, client_secret, websession=async_get_clientsession(hass)
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
        """Return hvac operation ie. heat, cool mode.
        Need to be one of HVAC_MODE_*.
        """
        if self._heater_data["heatingEnabled"]:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def icon(self):
        """Return nice icon for heater"""
        if self.hvac_mode == HVAC_MODE_HEAT:
            return "mdi:radiator"
        else:
            return "mdi:radiator-off"

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
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


######


API_URL = "https://api-1.adax.no/client-api"


class Adax:
    """Adax data handler."""

    def __init__(self, account_id, password, websession):
        """Init adax data handler."""
        self._account_id = account_id
        self._password = password
        self.websession = websession
        self._access_token = None
        self._rooms = []
        self._last_updated = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        self._timeout = 10

    async def get_rooms(self):
        """Get adax rooms."""
        await self.update()
        return self._rooms

    async def update(self, force_update=False):
        """Update data."""
        now = datetime.datetime.utcnow()
        if (
            now - self._last_updated < datetime.timedelta(seconds=30)
            and not force_update
        ):
            return
        self._last_updated = now
        await self.fetch_rooms_info()

    async def set_room_target_temperature(self, room_id, temperature, heating_enabled):
        """Set target temperature of the room."""
        json_data = {
            "rooms": [
                {
                    "id": room_id,
                    "heatingEnabled": heating_enabled,
                    "targetTemperature": str(int(temperature * 100)),
                }
            ]
        }
        await self._request(API_URL + "/rest/v1/control/", json_data=json_data)

    async def fetch_rooms_info(self):
        """Get rooms info."""
        response = await self._request(API_URL + "/rest/v1/content/")
        if response is None:
            return
        json_data = await response.json()
        if json_data is None:
            return
        self._rooms = json_data["rooms"]
        for room in self._rooms:
            room["targetTemperature"] = room.get("targetTemperature", 0) / 100.0
            room["temperature"] = room.get("temperature", 0) / 100.0

    async def _request(self, url, json_data=None, retry=3):
        if self._access_token is None:
            response = await self.websession.post(
                f"{API_URL}/auth/token",
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                data={
                    "grant_type": "password",
                    "username": self._account_id,
                    "password": self._password,
                },
            )
            token_data = json.loads(await response.text())
            self._access_token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            with async_timeout.timeout(self._timeout):
                if json_data:
                    response = await self.websession.post(
                        url, json=json_data, headers=headers
                    )
                else:
                    response = await self.websession.get(url, headers=headers)
            if response.status != 200:
                self._access_token = None
                if retry > 0:
                    await asyncio.sleep(1)
                    return await self._request(url, json_data, retry=retry - 1)
                _LOGGER.error(
                    "Error connecting to Adax, response: %s %s", response.status, response.reason
                )

                return None
        except aiohttp.ClientError as err:
            self._access_token = None
            if retry > 0:
                return await self._request(url, json_data, retry=retry - 1)
            _LOGGER.error("Error connecting to Adax: %s ", err, exc_info=True)
            raise
        except asyncio.TimeoutError:
            self._access_token = None
            if retry > 0:
                return await self._request(url, json_data, retry=retry - 1)
            _LOGGER.error("Timed out when connecting to Adax")
            raise
        return response
