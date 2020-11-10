"""Support for Adax wifi-enabled home heaters."""
import asyncio
import datetime
import json
import logging

import async_timeout
from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)

API_URL = "https://api-1.adax.no/client-api"
RATE_LIMIT_SECONDS = 5


class Adax:
    """Adax data handler."""

    def __init__(self, account_id, password, websession):
        """Init Adax data handler."""
        self._account_id = account_id
        self._password = password
        self.websession = websession
        self._access_token = None
        self._rooms = []
        self._timeout = 10

        self._prev_request = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        self._set_event = asyncio.Event()
        self._write_task = None
        self._pending_writes = {"rooms": []}

    async def get_rooms(self):
        """Get Adax rooms."""
        await self.update()
        return self._rooms

    async def update(self):
        """Update data."""
        if (
            datetime.datetime.utcnow() - self._prev_request < datetime.timedelta(seconds=RATE_LIMIT_SECONDS)
            or self._write_task is not None
        ):
            _LOGGER.debug("Skip update")
            return
        await self.fetch_rooms_info()

    async def set_room_target_temperature(self, room_id, temperature, heating_enabled):
        """Set target temperature of the room."""
        if self._write_task is not None:
            self._write_task.cancel()
        self._pending_writes["rooms"] = [
            room
            for room in self._pending_writes["rooms"]
            if not room.get("id") == room_id
        ]

        self._pending_writes["rooms"].append(
            {
                "id": room_id,
                "heatingEnabled": heating_enabled,
                "targetTemperature": str(int(temperature * 100)),
            }
        )

        self._write_task = asyncio.ensure_future(
            self._write_set_room_target_temperature(self._pending_writes.copy())
        )
        await self._set_event.wait()

    async def _write_set_room_target_temperature(self, json_data):
        now = datetime.datetime.utcnow()
        delay = max(
            0.1,
            (
                self._prev_request
                + datetime.timedelta(seconds=RATE_LIMIT_SECONDS)
                - now
            ).total_seconds(),
        )
        _LOGGER.debug("Delaying request %.1fs", delay)
        await asyncio.sleep(delay)
        if await self._request(API_URL + "/rest/v1/control/", json_data=json_data) is not None:
            for room_i in self._rooms.copy():
                for room_j in json_data.get("rooms"):
                    if room_i["id"] == room_j["id"]:
                        room_i["targetTemperature"] = (
                            float(room_j.get("targetTemperature", 0)) / 100.0
                        )
                        break

        self._pending_writes = {"rooms": []}
        self._set_event.set()
        self._set_event.clear()
        self._write_task = None

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
        self._prev_request = datetime.datetime.utcnow()
        _LOGGER.debug("Request %s %s, %s", url, retry, json_data)
        if self._access_token is None:
            self._access_token = await get_adax_token(
                self.websession, self._account_id, self._password
            )
            if self._access_token is None:
                return None

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
                    if response.status == 429:
                        _LOGGER.warning("Too many requests, will retry")
                        await asyncio.sleep(RATE_LIMIT_SECONDS * max(1, (4 - retry)))
                    return await self._request(url, json_data, retry=retry - 1)
                _LOGGER.error(
                    "Error connecting to Adax, response: %s %s",
                    response.status,
                    response.reason,
                )
                return None
        except ClientError as err:
            self._access_token = None
            if retry > 0 and "429" not in str(err):
                return await self._request(url, json_data, retry=retry - 1)
            _LOGGER.error("Error connecting to Adax: %s ", err, exc_info=True)
            raise
        except asyncio.TimeoutError:
            self._access_token = None
            if retry > 0:
                return await self._request(url, json_data, retry=retry - 1)
            _LOGGER.error("Timed out when connecting to Adax")
            raise
        self._prev_request = datetime.datetime.utcnow()
        return response


async def get_adax_token(websession, account_id, password, retry=3, timeout=10):
    """Get token for Adax."""
    try:
        with async_timeout.timeout(timeout):
            response = await websession.post(
                f"{API_URL}/auth/token",
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                data={
                    "grant_type": "password",
                    "username": account_id,
                    "password": password,
                },
            )
    except ClientError as err:
        if retry > 0:
            return await get_adax_token(websession, account_id, password, retry=retry - 1)
        _LOGGER.error("Error getting token Adax: %s ", err, exc_info=True)
        return None
    except asyncio.TimeoutError:
        if retry > 0:
            return await get_adax_token(websession, account_id, password, retry=retry - 1)
        _LOGGER.error("Timed out when connecting to Adax for token")
        return None
    if response.status != 200:
        if "invalid_grant" in response.reason:
            log_str = "https://github.com/Danielhiversen/home_assistant_adax/issues/18#issuecomment-707238234"
        else:
            log_str = ""
        _LOGGER.error(
            "Adax: Failed to login to retrieve token: %s %s %s",
            response.status,
            response.reason,
            log_str,
        )
        return None
    token_data = json.loads(await response.text())
    return token_data.get("access_token")
