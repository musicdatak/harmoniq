"""MusicBrainz integration — rate-limited recording lookup."""

import asyncio
import time

import httpx

from app.config import settings

MUSICBRAINZ_API = "https://musicbrainz.org/ws/2"
MIN_REQUEST_INTERVAL = 1.1  # seconds between requests (mandatory)


class MusicBrainzClient:
    """Singleton MusicBrainz client with global rate limiting."""

    _instance: "MusicBrainzClient | None" = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    def __new__(cls) -> "MusicBrainzClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _rate_limit(self) -> None:
        """Enforce minimum interval between requests."""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL:
                await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_time = time.monotonic()

    async def lookup_recording(self, artist: str, title: str) -> dict | None:
        """Search MusicBrainz for a recording by artist + title.

        Returns dict with musicbrainz_id, tags, score, or None if not found.
        """
        await self._rate_limit()

        query = f'recording:"{title}" AND artist:"{artist}"'
        params = {
            "query": query,
            "fmt": "json",
            "limit": "1",
        }
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{MUSICBRAINZ_API}/recording",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        recordings = data.get("recordings", [])
        if not recordings:
            return None

        rec = recordings[0]
        score = rec.get("score", 0)

        # Only accept high-confidence matches
        if score < 80:
            return None

        tags = [t["name"] for t in rec.get("tags", [])] if rec.get("tags") else []

        return {
            "musicbrainz_id": rec["id"],
            "tags": tags,
            "score": score,
        }


# Module-level singleton
mb_client = MusicBrainzClient()
