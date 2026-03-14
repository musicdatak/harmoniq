import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PlaylistCreate(BaseModel):
    name: str
    description: str | None = None


class PlaylistUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    harmony_weight: int | None = None
    energy_weight: int | None = None
    bpm_weight: int | None = None
    energy_arc_mode: bool | None = None


class TrackResponse(BaseModel):
    id: uuid.UUID
    title: str
    artist: str
    musicbrainz_id: str | None = None
    key_musical: str | None = None
    key_camelot: str | None = None
    key_confidence: Decimal | None = None
    bpm: Decimal | None = None
    bpm_confidence: Decimal | None = None
    energy: Decimal | None = None
    loudness: Decimal | None = None
    danceability: Decimal | None = None
    genre: str | None = None
    analysis_source: str | None = None
    enrichment_status: str = "pending"

    model_config = {"from_attributes": True}


class PlaylistTrackResponse(BaseModel):
    id: uuid.UUID
    playlist_id: uuid.UUID
    track_id: uuid.UUID
    position_original: int | None = None
    position_scheduled: int | None = None
    key_override: str | None = None
    bpm_override: Decimal | None = None
    energy_override: int | None = None
    transition_score: Decimal | None = None
    transition_label: str | None = None
    track: TrackResponse

    model_config = {"from_attributes": True}


class PlaylistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    harmony_weight: int
    energy_weight: int
    bpm_weight: int
    energy_arc_mode: bool
    mix_score: Decimal | None = None
    is_scheduled: bool
    created_at: datetime
    updated_at: datetime
    track_count: int = 0

    model_config = {"from_attributes": True}


class PlaylistDetailResponse(PlaylistResponse):
    tracks: list[PlaylistTrackResponse] = []


class ImportTextRequest(BaseModel):
    text: str


class TrackOverrideUpdate(BaseModel):
    key_override: str | None = None
    bpm_override: Decimal | None = None
    energy_override: int | None = None
