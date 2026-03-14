"""Deezer API integration — free BPM lookup, no auth required."""

import asyncio
import time

import httpx

DEEZER_API = "https://api.deezer.com"
MIN_REQUEST_INTERVAL = 0.2  # 5 req/s to be safe


class DeezerClient:
    """Rate-limited Deezer API client."""

    _instance: "DeezerClient | None" = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    def __new__(cls) -> "DeezerClient":
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

    async def search_track(self, artist: str, title: str) -> dict | None:
        """Search Deezer for a track, return BPM and metadata if found."""
        await self._rate_limit()

        query = f'artist:"{artist}" track:"{title}"'
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{DEEZER_API}/search",
                    params={"q": query, "limit": "1"},
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        tracks = data.get("data", [])
        if not tracks:
            return None

        track = tracks[0]
        deezer_id = track.get("id")
        if not deezer_id:
            return None

        # Fetch full track details (search results don't always include BPM)
        return await self._get_track_details(deezer_id)

    async def _get_track_details(self, track_id: int) -> dict | None:
        """Fetch full track details including BPM."""
        await self._rate_limit()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{DEEZER_API}/track/{track_id}")
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        if data.get("error"):
            return None

        bpm = data.get("bpm")
        # Deezer sometimes returns 0 for BPM
        if bpm and bpm > 0:
            return {
                "bpm": float(bpm),
                "deezer_id": data.get("id"),
                "isrc": data.get("isrc"),
                "gain": data.get("gain"),
            }

        return None


deezer_client = DeezerClient()
