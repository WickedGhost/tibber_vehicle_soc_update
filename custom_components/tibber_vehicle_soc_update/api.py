from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import APP_HEADERS, TIBBER_GRAPHQL_URL, TIBBER_LOGIN_URL


class TibberVehicleSocApiError(Exception):
    """Raised when Tibber API calls fail."""


class TibberVehicleSocApi:
    """Minimal Tibber API client for updating the offline vehicle SoC."""

    def __init__(self, session: ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None

    async def async_validate_auth(self, home_id: str) -> None:
        """Validate credentials and home access during config flow."""
        homes = await self.async_get_homes()
        known_home_ids = {home["id"] for home in homes if "id" in home}
        if home_id not in known_home_ids:
            raise TibberVehicleSocApiError("Configured home ID was not returned by Tibber")

    async def async_get_homes(self) -> list[dict[str, Any]]:
        """Return available homes for the authenticated Tibber user."""
        query = """
        query {
          me {
            homes {
              id
            }
          }
        }
        """
        data = await self._async_execute_gql(query)
        return data.get("me", {}).get("homes", [])

    async def async_set_vehicle_soc(self, home_id: str, vehicle_id: str, soc: int) -> None:
        """Update the offline vehicle battery level in Tibber."""
        mutation = """
        mutation SetVehicleSettings($vehicleId: String!, $homeId: String!, $settings: [SettingsItemInput!]) {
          me {
            setVehicleSettings(id: $vehicleId, homeId: $homeId, settings: $settings) {
              __typename
            }
          }
        }
        """

        await self._async_execute_gql(
            mutation,
            {
                "vehicleId": vehicle_id,
                "homeId": home_id,
                "settings": [
                    {
                        "key": "offline.vehicle.batteryLevel",
                        "value": int(soc),
                    }
                ],
            },
        )

    async def _async_execute_gql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a Tibber GraphQL request."""
        token = await self._async_get_token()
        headers = {
            **APP_HEADERS,
            "Accept": "application/graphql-response+json, application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._session.post(
                TIBBER_GRAPHQL_URL,
                json={"query": query, "variables": variables or {}},
                headers=headers,
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise TibberVehicleSocApiError(f"GraphQL request failed: {err}") from err

        if "errors" in payload:
            raise TibberVehicleSocApiError(str(payload["errors"]))

        data = payload.get("data")
        if data is None:
            raise TibberVehicleSocApiError(f"No data returned from Tibber GraphQL: {payload}")

        return data

    async def _async_get_token(self) -> str:
        """Authenticate against Tibber and cache the bearer token."""
        if self._token is not None:
            return self._token

        headers = {
            **APP_HEADERS,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with self._session.post(
                TIBBER_LOGIN_URL,
                data={"email": self._email, "password": self._password},
                headers=headers,
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise TibberVehicleSocApiError(f"Login failed: {err}") from err

        token = payload.get("token")
        if not token:
            raise TibberVehicleSocApiError("No token returned from Tibber login")

        self._token = token
        return token