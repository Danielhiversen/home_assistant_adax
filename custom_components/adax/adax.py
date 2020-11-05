"""Support for Adax wifi-enabled home heaters."""
import asyncio
import datetime
import json
import logging

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

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

        self._next_request = datetime.datetime.now()
        self._set_event = asyncio.Event()
        self._write_task = None
        self._pending_writes = {"rooms": []}

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
        now = datetime.datetime.now()
        sleep = max(
            0.5,
            (self._next_request - now).total_seconds(),
            (self._last_updated + datetime.timedelta(seconds=15) - now).total_seconds(),
        )
        print(
            sleep,
            json_data,
            (self._next_request - now).total_seconds(),
            (self._last_updated + datetime.timedelta(seconds=15) - now).total_seconds(),
        )
        await asyncio.sleep(sleep)
        print("aaa")
        await self._request(API_URL + "/rest/v1/control/", json_data=json_data)
        self._next_request = now + datetime.timedelta(seconds=15)
        self._last_updated = now
        self._pending_writes = {"rooms": []}
        self._set_event.set()
        self._set_event.clear()

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
        print(url, retry)
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
                if retry > 0 and response.status != 429:
                    await asyncio.sleep(1)
                    return await self._request(url, json_data, retry=retry - 1)
                _LOGGER.error(
                    "Error connecting to Adax, response: %s %s",
                    response.status,
                    response.reason,
                )

                return None
        except aiohttp.ClientError as err:
            self._access_token = None
            if retry > 0 and "429" not in err:
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


async def get_adax_token(websession, account_id, password):
    """Get token for Adax."""
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
