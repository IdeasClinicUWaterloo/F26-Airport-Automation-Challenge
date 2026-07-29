"""Fetch aircraft state vectors from the OpenSky Network REST API.

Set `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` to use OAuth authentication.
"""

import os
import time

import requests

STATES_URL = "https://opensky-network.org/api/states/all"
TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/"
    "opensky-network/protocol/openid-connect/token"
)

STATE_FIELDS = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source", "category",
]


class OpenSkyClient:
    def __init__(self, client_id=None, client_secret=None):
        self.client_id = client_id or os.environ.get("OPENSKY_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("OPENSKY_CLIENT_SECRET")
        self._token = None
        self._token_expiry = 0

    def _get_token(self):
        if self._token and time.time() < self._token_expiry:
            return self._token

        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        self._token = payload["access_token"]
        self._token_expiry = time.time() + payload.get("expires_in", 1800) - 30
        return self._token

    def fetch_states(self, bbox=None):
        """Fetch positioned aircraft inside an optional bounding box."""

        params = {}
        if bbox is not None:
            lamin, lomin, lamax, lomax = bbox
            params.update(lamin=lamin, lomin=lomin, lamax=lamax, lomax=lomax)

        headers = {}
        if self.client_id and self.client_secret:
            headers["Authorization"] = f"Bearer {self._get_token()}"

        response = requests.get(STATES_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()

        states = []
        for raw in payload.get("states") or []:
            state = dict(zip(STATE_FIELDS, raw))
            if state["latitude"] is None or state["longitude"] is None:
                continue
            states.append(state)

        return states
