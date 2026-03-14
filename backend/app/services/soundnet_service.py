"""SoundNet Track Analysis API integration via RapidAPI.

Provides BPM, key (Camelot), energy, and danceability lookups by artist + title.
Requires a RapidAPI key — set RAPIDAPI_KEY in env or .env file.
"""

import asyncio
import time

import httpx

from app.config import settings
from app.engine.camelot import parse_key

SOUNDNET_HOST = "track-analysis.p.rapidapi.com"
SOUNDNET_BASE = f"https://{SOUNDNET_HOST}"
MIN_REQUEST_INTERVAL = 1.0  # stay safe with rate limits


class SoundNetClient:
    """Rate-limited SoundNet Track Analysis API client (singleton)."""

    _instance: "SoundNetClient | None" = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    def __new__(cls) -> "SoundNetClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @property
    def api_key(self) -> str:
        return settings.RAPIDAPI_KEY

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def _rate_limit(self) -> None:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_time = time.monotonic()

    async def search_track(self, artist: str, title: str) -> dict | None:
        """Search SoundNet for a track, return key + BPM + extras if found.

        Returns dict with keys: camelot, key_musical, bpm, energy, danceability
        or None if not found / error.
        """
        if not self.available:
            return None

        await self._rate_limit()

        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": SOUNDNET_HOST,
            "Content-Type": "application/json",
        }
        params = {
            "song": title,
            "artist": artist,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{SOUNDNET_BASE}/pktx/analysis",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        return self._parse_response(data)

    def _parse_response(self, data: dict) -> dict | None:
        """Extract key, BPM, energy, danceability from SoundNet response."""
        if not data:
            return None

        result = {}

        # BPM
        bpm = data.get("bpm") or data.get("tempo")
        if bpm:
            try:
                bpm_val = float(bpm)
                if bpm_val > 0:
                    result["bpm"] = bpm_val
            except (ValueError, TypeError):
                pass

        # Key — try camelot field first, then key field
        camelot_raw = data.get("camelot") or data.get("camelot_key")
        key_raw = data.get("key") or data.get("key_of")

        camelot = None
        if camelot_raw:
            camelot = parse_key(str(camelot_raw).strip())
        if not camelot and key_raw:
            camelot = parse_key(str(key_raw).strip())

        if camelot:
            result["camelot"] = camelot
            result["key_musical"] = str(key_raw or camelot_raw or "")

        # Energy
        energy = data.get("energy")
        if energy is not None:
            try:
                energy_val = float(energy)
                if 0 <= energy_val <= 1:
                    result["energy"] = energy_val
            except (ValueError, TypeError):
                pass

        # Danceability
        danceability = data.get("danceability")
        if danceability is not None:
            try:
                dance_val = float(danceability)
                if 0 <= dance_val <= 1:
                    result["danceability"] = dance_val
            except (ValueError, TypeError):
                pass

        if not result:
            return None

        return result


soundnet_client = SoundNetClient()
