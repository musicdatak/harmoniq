"""GetSongBPM API integration — key + BPM lookup.

Requires a free API key from https://getsongbpm.com/api
Set GETSONGBPM_API_KEY in env or .env file.
"""

import asyncio
import re
import time

import httpx

from app.config import settings

GETSONGBPM_API = "https://api.getsongbpm.com"
MIN_REQUEST_INTERVAL = 1.2  # ~3000 req/hour = ~0.83/s, stay safe


def _open_key_to_camelot(open_key: str) -> str | None:
    """Convert Open Key notation to Camelot code.

    Open Key uses: 1d-12d (minor) and 1m-12m (major)
    Camelot uses:  1A-12A (minor) and 1B-12B (major)

    Some APIs return Camelot directly (1A, 1B) — handle both.
    """
    if not open_key:
        return None

    ok = open_key.strip()

    # Already Camelot format (e.g., "8A", "11B")
    m = re.match(r"^(\d{1,2})([ABab])$", ok)
    if m:
        return f"{m.group(1)}{m.group(2).upper()}"

    # Open Key format (e.g., "8d", "11m")
    m = re.match(r"^(\d{1,2})([dDmM])$", ok)
    if m:
        num = m.group(1)
        letter = m.group(2).lower()
        # d = minor = A, m = major = B
        camelot_letter = "A" if letter == "d" else "B"
        return f"{num}{camelot_letter}"

    return None


def _musical_key_to_camelot(key_of: str) -> str | None:
    """Convert musical key string like 'Am', 'C', 'F#m' to Camelot code."""
    from app.engine.camelot import parse_key
    if not key_of:
        return None
    return parse_key(key_of.strip())


class GetSongBPMClient:
    """Rate-limited GetSongBPM API client."""

    _instance: "GetSongBPMClient | None" = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float = 0.0

    def __new__(cls) -> "GetSongBPMClient":
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
        return settings.GETSONGBPM_API_KEY

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
        """Search GetSongBPM for a track, return key + BPM if found.

        Returns dict with keys: camelot, key_musical, bpm, or None.
        """
        if not self.available:
            return None

        await self._rate_limit()

        params = {
            "api_key": self.api_key,
            "type": "song",
            "lookup": f"song:{title} artist:{artist}",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{GETSONGBPM_API}/search/",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        # Response has "search" array
        results = data.get("search", [])
        if not results:
            return None

        song = results[0]
        song_id = song.get("id")
        if not song_id:
            return None

        # Fetch full song details
        return await self._get_song_details(song_id)

    async def _get_song_details(self, song_id: str) -> dict | None:
        """Fetch full song details including key and BPM."""
        await self._rate_limit()

        params = {
            "api_key": self.api_key,
            "id": song_id,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{GETSONGBPM_API}/song/",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, Exception):
            return None

        song = data.get("song", {})
        if not song:
            return None

        result = {}

        # BPM
        tempo = song.get("tempo")
        if tempo:
            try:
                bpm = float(tempo)
                if bpm > 0:
                    result["bpm"] = bpm
            except (ValueError, TypeError):
                pass

        # Key — try open_key first (more structured), then key_of
        open_key = song.get("open_key")
        key_of = song.get("key_of")

        camelot = _open_key_to_camelot(open_key)
        if not camelot and key_of:
            camelot = _musical_key_to_camelot(key_of)

        if camelot:
            result["camelot"] = camelot
            result["key_musical"] = key_of or ""

        if not result:
            return None

        return result


getsongbpm_client = GetSongBPMClient()
