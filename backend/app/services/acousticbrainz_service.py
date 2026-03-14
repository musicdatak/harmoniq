"""AcousticBrainz integration — key + BPM lookup by MusicBrainz recording ID.

AcousticBrainz is a read-only archive (data collection ended 2022).
The API may be unavailable — all calls handle failures gracefully.
"""

import asyncio
import time

import httpx

ACOUSTICBRAINZ_API = "https://acousticbrainz.org/api/v1"
MIN_REQUEST_INTERVAL = 1.0  # 10 req/10s limit


class AcousticBrainzClient:
    """Rate-limited AcousticBrainz API client."""

    _instance: "AcousticBrainzClient | None" = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    def __new__(cls) -> "AcousticBrainzClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _rate_limit(self) -> None:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_time = time.monotonic()

    async def lookup_by_mbid(self, mbid: str) -> dict | None:
        """Fetch low-level audio features by MusicBrainz recording ID.

        Returns dict with key, scale, bpm, energy, danceability, loudness or None.
        """
        await self._rate_limit()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{ACOUSTICBRAINZ_API}/{mbid}/low-level",
                    params={"features": "rhythm;tonal"},
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        result = {}

        # Extract key
        tonal = data.get("tonal", {})
        key = tonal.get("key_key")
        scale = tonal.get("key_scale")
        if key and scale:
            result["key"] = key
            result["scale"] = scale
            result["key_confidence"] = tonal.get("key_strength")

        # Extract BPM
        rhythm = data.get("rhythm", {})
        bpm = rhythm.get("bpm")
        if bpm and bpm > 0:
            result["bpm"] = float(bpm)

        # Extract energy/loudness
        lowlevel = data.get("lowlevel", {})
        if "average_loudness" in lowlevel:
            result["loudness"] = float(lowlevel["average_loudness"])

        if not result:
            return None

        return result


ab_client = AcousticBrainzClient()
