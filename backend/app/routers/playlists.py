"""Playlist CRUD, import, and enrichment endpoints."""

import uuid
from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session, get_db
from app.engine.scheduler import TrackData, schedule_playlist, transition_score
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.models.track import Track
from app.models.user import User
from app.schemas.playlist import (
    ImportTextRequest,
    PlaylistCreate,
    PlaylistDetailResponse,
    PlaylistResponse,
    PlaylistUpdate,
)
from app.services.auth_service import get_current_user
from app.services.import_service import parse_excel, parse_text
from app.services.musicbrainz_service import mb_client
from app.services.deezer_service import deezer_client
from app.services.acousticbrainz_service import ab_client
from app.services.getsongbpm_service import getsongbpm_client
from app.engine.camelot import classify_transition, musical_to_camelot, parse_key

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


async def _get_or_create_track(db: AsyncSession, artist: str, title: str, extra: dict | None = None) -> Track:
    """Find existing track by case-insensitive artist+title, or create new."""
    result = await db.execute(
        select(Track).where(
            func.lower(Track.artist) == artist.lower(),
            func.lower(Track.title) == title.lower(),
        )
    )
    track = result.scalar_one_or_none()
    if track:
        return track

    extra = extra or {}
    key_raw = extra.get("key")
    camelot = parse_key(key_raw) if key_raw else None

    track = Track(
        title=title,
        artist=artist,
        key_camelot=camelot,
        key_musical=key_raw if camelot else None,
        bpm=extra.get("bpm"),
        energy=extra.get("energy"),
        analysis_source="cache" if (camelot or extra.get("bpm")) else None,
        enrichment_status="analyzed" if camelot else "pending",
    )
    db.add(track)
    await db.flush()
    return track


async def _import_tracks(db: AsyncSession, playlist: Playlist, parsed: list[dict]) -> list[PlaylistTrack]:
    """Import parsed tracks into a playlist, reusing existing tracks."""
    playlist_tracks = []
    for idx, item in enumerate(parsed):
        track = await _get_or_create_track(
            db, item["artist"], item["title"],
            {k: v for k, v in item.items() if k not in ("artist", "title")},
        )
        # Check if this track is already in the playlist
        existing_pt = await db.execute(
            select(PlaylistTrack).where(
                PlaylistTrack.playlist_id == playlist.id,
                PlaylistTrack.track_id == track.id,
            )
        )
        if existing_pt.scalar_one_or_none():
            continue

        pt = PlaylistTrack(
            playlist_id=playlist.id,
            track_id=track.id,
            position_original=idx + 1,
        )
        db.add(pt)
        playlist_tracks.append(pt)

    await db.flush()
    return playlist_tracks


def _playlist_to_response(playlist: Playlist, track_count: int = 0) -> dict:
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "harmony_weight": playlist.harmony_weight,
        "energy_weight": playlist.energy_weight,
        "bpm_weight": playlist.bpm_weight,
        "energy_arc_mode": playlist.energy_arc_mode,
        "mix_score": playlist.mix_score,
        "is_scheduled": playlist.is_scheduled,
        "created_at": playlist.created_at,
        "updated_at": playlist.updated_at,
        "track_count": track_count,
    }


@router.get("", response_model=list[PlaylistResponse])
async def list_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist, func.count(PlaylistTrack.id).label("track_count"))
        .outerjoin(PlaylistTrack)
        .where(Playlist.user_id == current_user.id)
        .group_by(Playlist.id)
        .order_by(Playlist.updated_at.desc())
    )
    rows = result.all()
    return [_playlist_to_response(row[0], row[1]) for row in rows]


@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    body: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    playlist = Playlist(user_id=current_user.id, name=body.name, description=body.description)
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return _playlist_to_response(playlist, 0)


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
        .where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    pts = sorted(playlist.playlist_tracks, key=lambda pt: pt.position_scheduled or pt.position_original or 0)
    return {
        **_playlist_to_response(playlist, len(pts)),
        "tracks": pts,
    }


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: uuid.UUID,
    body: PlaylistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(playlist, field, value)

    await db.commit()
    await db.refresh(playlist)

    count_result = await db.execute(
        select(func.count(PlaylistTrack.id)).where(PlaylistTrack.playlist_id == playlist.id)
    )
    track_count = count_result.scalar() or 0
    return _playlist_to_response(playlist, track_count)


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    await db.delete(playlist)
    await db.commit()


@router.post("/{playlist_id}/import/text", response_model=PlaylistDetailResponse)
async def import_text(
    playlist_id: uuid.UUID,
    body: ImportTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    parsed = parse_text(body.text)
    if not parsed:
        raise HTTPException(status_code=400, detail="No tracks found in text")

    await _import_tracks(db, playlist, parsed)
    await db.commit()

    # Reload with tracks
    return await get_playlist(playlist_id, current_user, db)


@router.post("/{playlist_id}/import/excel", response_model=PlaylistDetailResponse)
async def import_excel(
    playlist_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    file_bytes = await file.read()
    parsed = parse_excel(file_bytes, file.filename or "upload.xlsx")
    if not parsed:
        raise HTTPException(status_code=400, detail="No tracks found in file")

    await _import_tracks(db, playlist, parsed)
    await db.commit()

    return await get_playlist(playlist_id, current_user, db)


# --- Enrichment ---

async def _enrich_musicbrainz_task(playlist_id: uuid.UUID) -> None:
    """Background task: query MusicBrainz for each pending track in the playlist."""
    async with async_session() as db:
        result = await db.execute(
            select(PlaylistTrack)
            .options(selectinload(PlaylistTrack.track))
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
        pts = result.scalars().all()

        for pt in pts:
            track = pt.track
            if track.musicbrainz_id or track.enrichment_status == "not_found":
                continue

            lookup = await mb_client.lookup_recording(track.artist, track.title)
            if lookup:
                track.musicbrainz_id = lookup["musicbrainz_id"]
                track.enrichment_status = "identified"
                if lookup["tags"]:
                    track.genre = ", ".join(lookup["tags"][:3])
                track.enriched_at = datetime.utcnow()
            else:
                track.enrichment_status = "not_found"

            await db.commit()


@router.post("/{playlist_id}/enrich/musicbrainz")
async def enrich_musicbrainz(
    playlist_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    background_tasks.add_task(_enrich_musicbrainz_task, playlist_id)
    return {"status": "enrichment_started"}


@router.get("/{playlist_id}/enrich/status")
async def enrich_status(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    result = await db.execute(
        select(PlaylistTrack)
        .options(selectinload(PlaylistTrack.track))
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    pts = result.scalars().all()

    total = len(pts)
    identified = sum(1 for pt in pts if pt.track.musicbrainz_id)
    analyzed = sum(1 for pt in pts if pt.track.key_camelot)
    has_bpm = sum(1 for pt in pts if pt.track.bpm is not None)
    not_found = sum(1 for pt in pts if pt.track.enrichment_status == "not_found")
    pending = total - identified - not_found

    return {
        "total": total,
        "identified": identified,
        "analyzed": analyzed,
        "has_bpm": has_bpm,
        "pending": pending,
        "not_found": not_found,
    }


# --- Deezer BPM enrichment ---

async def _enrich_deezer_task(playlist_id: uuid.UUID) -> None:
    """Background task: query Deezer for BPM on tracks missing it."""
    async with async_session() as db:
        result = await db.execute(
            select(PlaylistTrack)
            .options(selectinload(PlaylistTrack.track))
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
        pts = result.scalars().all()

        for pt in pts:
            track = pt.track
            # Skip tracks that already have BPM
            if track.bpm is not None:
                continue

            lookup = await deezer_client.search_track(track.artist, track.title)
            if lookup and lookup.get("bpm"):
                track.bpm = Decimal(str(round(lookup["bpm"], 2)))
                if not track.analysis_source:
                    track.analysis_source = "deezer"
                if track.enrichment_status == "identified":
                    # Keep identified, but now has data
                    pass
                elif track.enrichment_status == "pending":
                    track.enrichment_status = "identified"
                track.enriched_at = datetime.utcnow()

            await db.commit()


@router.post("/{playlist_id}/enrich/deezer")
async def enrich_deezer(
    playlist_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    background_tasks.add_task(_enrich_deezer_task, playlist_id)
    return {"status": "deezer_enrichment_started"}


# --- AcousticBrainz key+BPM enrichment ---

async def _enrich_acousticbrainz_task(playlist_id: uuid.UUID) -> None:
    """Background task: query AcousticBrainz for key+BPM using MusicBrainz IDs."""
    async with async_session() as db:
        result = await db.execute(
            select(PlaylistTrack)
            .options(selectinload(PlaylistTrack.track))
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
        pts = result.scalars().all()

        for pt in pts:
            track = pt.track
            # Need MBID and missing key data
            if not track.musicbrainz_id:
                continue
            if track.key_camelot and track.bpm is not None:
                continue

            lookup = await ab_client.lookup_by_mbid(track.musicbrainz_id)
            if not lookup:
                continue

            # Set key if missing
            if not track.key_camelot and lookup.get("key") and lookup.get("scale"):
                camelot = musical_to_camelot(lookup["key"], lookup["scale"])
                if camelot:
                    track.key_camelot = camelot
                    track.key_musical = f"{lookup['key']} {lookup['scale']}"
                    if lookup.get("key_confidence") is not None:
                        track.key_confidence = Decimal(str(round(lookup["key_confidence"], 4)))

            # Set BPM if missing
            if track.bpm is None and lookup.get("bpm"):
                track.bpm = Decimal(str(round(lookup["bpm"], 2)))

            # Set loudness if missing
            if track.loudness is None and lookup.get("loudness") is not None:
                track.loudness = Decimal(str(round(lookup["loudness"], 4)))

            if not track.analysis_source:
                track.analysis_source = "acousticbrainz"
            if track.key_camelot:
                track.enrichment_status = "analyzed"
            track.enriched_at = datetime.utcnow()

            await db.commit()


@router.post("/{playlist_id}/enrich/acousticbrainz")
async def enrich_acousticbrainz(
    playlist_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    background_tasks.add_task(_enrich_acousticbrainz_task, playlist_id)
    return {"status": "acousticbrainz_enrichment_started"}


# --- GetSongBPM key+BPM enrichment ---

async def _enrich_getsongbpm_task(playlist_id: uuid.UUID) -> None:
    """Background task: query GetSongBPM for key + BPM on tracks missing them."""
    if not getsongbpm_client.available:
        return

    async with async_session() as db:
        result = await db.execute(
            select(PlaylistTrack)
            .options(selectinload(PlaylistTrack.track))
            .where(PlaylistTrack.playlist_id == playlist_id)
        )
        pts = result.scalars().all()

        for pt in pts:
            track = pt.track
            # Skip tracks that already have both key and BPM
            if track.key_camelot and track.bpm is not None:
                continue

            lookup = await getsongbpm_client.search_track(track.artist, track.title)
            if not lookup:
                continue

            if not track.key_camelot and lookup.get("camelot"):
                track.key_camelot = lookup["camelot"]
                if lookup.get("key_musical"):
                    track.key_musical = lookup["key_musical"]

            if track.bpm is None and lookup.get("bpm"):
                track.bpm = Decimal(str(round(lookup["bpm"], 2)))

            if not track.analysis_source or track.analysis_source in ("deezer",):
                track.analysis_source = "getsongbpm"
            if track.key_camelot:
                track.enrichment_status = "analyzed"
            track.enriched_at = datetime.utcnow()

            await db.commit()


@router.post("/{playlist_id}/enrich/getsongbpm")
async def enrich_getsongbpm(
    playlist_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not getsongbpm_client.available:
        raise HTTPException(
            status_code=400,
            detail="GetSongBPM API key not configured. Set GETSONGBPM_API_KEY in environment.",
        )

    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    background_tasks.add_task(_enrich_getsongbpm_task, playlist_id)
    return {"status": "getsongbpm_enrichment_started"}


# --- Combined auto-enrich (all sources) ---

async def _enrich_all_task(playlist_id: uuid.UUID) -> None:
    """Chain all enrichment sources: MusicBrainz → GetSongBPM → AcousticBrainz → Deezer."""
    await _enrich_musicbrainz_task(playlist_id)
    await _enrich_getsongbpm_task(playlist_id)
    await _enrich_acousticbrainz_task(playlist_id)
    await _enrich_deezer_task(playlist_id)


@router.post("/{playlist_id}/enrich/auto")
async def enrich_auto(
    playlist_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run all enrichment sources: MusicBrainz → GetSongBPM → AcousticBrainz → Deezer."""
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    background_tasks.add_task(_enrich_all_task, playlist_id)
    return {"status": "auto_enrichment_started"}


# --- Scheduling ---

def _effective(pt: PlaylistTrack, field: str):
    """Get effective value: override if set, else track's value."""
    override = getattr(pt, f"{field}_override", None)
    if override is not None:
        return override
    return getattr(pt.track, field, None)


def _to_float(val) -> float | None:
    if val is None:
        return None
    return float(val)


@router.post("/{playlist_id}/schedule", response_model=PlaylistDetailResponse)
async def schedule(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playlist)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
        .where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    pts = playlist.playlist_tracks
    if not pts:
        raise HTTPException(status_code=400, detail="No tracks to schedule")

    # Build TrackData list with effective values
    pt_map: dict[str, PlaylistTrack] = {}
    track_datas: list[TrackData] = []
    for pt in pts:
        eff_key = _effective(pt, "key") if pt.key_override else pt.track.key_camelot
        # key_override is already a camelot code; track.key_camelot is too
        camelot = pt.key_override or pt.track.key_camelot
        td = TrackData(
            id=str(pt.track.id),
            title=pt.track.title,
            artist=pt.track.artist,
            camelot=camelot,
            bpm=_to_float(pt.bpm_override if pt.bpm_override is not None else pt.track.bpm),
            energy=_to_float(pt.energy_override if pt.energy_override is not None else pt.track.energy),
        )
        track_datas.append(td)
        pt_map[str(pt.track.id)] = pt

    weights = {
        "harmony": playlist.harmony_weight,
        "energy": playlist.energy_weight,
        "bpm": playlist.bpm_weight,
    }

    # Run scheduler
    scheduled = schedule_playlist(track_datas, weights, playlist.energy_arc_mode)

    # Update positions, transition scores
    total_score = 0.0
    scored_count = 0
    for i, td in enumerate(scheduled):
        pt = pt_map[td.id]
        pt.position_scheduled = i + 1

        if i > 0:
            prev_td = scheduled[i - 1]
            pos_ratio = i / len(scheduled) if playlist.energy_arc_mode else None
            score = transition_score(prev_td, td, weights, pos_ratio)
            pt.transition_score = Decimal(str(round(score, 2)))
            pt.transition_label = classify_transition(prev_td.camelot, td.camelot) if (prev_td.camelot and td.camelot) else None
            total_score += score
            scored_count += 1
        else:
            pt.transition_score = None
            pt.transition_label = None

    # Calculate mix score
    playlist.mix_score = Decimal(str(round(total_score / scored_count, 2))) if scored_count > 0 else None
    playlist.is_scheduled = True

    await db.commit()

    return await get_playlist(playlist_id, current_user, db)


# --- Export ---

@router.get("/{playlist_id}/export/excel")
async def export_excel(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.export_service import generate_excel

    result = await db.execute(
        select(Playlist)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
        .where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    pts = sorted(playlist.playlist_tracks, key=lambda pt: pt.position_scheduled or pt.position_original or 0)

    tracks_data = []
    for pt in pts:
        tracks_data.append({
            "position": pt.position_scheduled or pt.position_original,
            "title": pt.track.title,
            "artist": pt.track.artist,
            "key_camelot": pt.key_override or pt.track.key_camelot,
            "key_musical": pt.track.key_musical,
            "bpm": pt.bpm_override if pt.bpm_override is not None else pt.track.bpm,
            "energy": pt.energy_override if pt.energy_override is not None else pt.track.energy,
            "transition_score": pt.transition_score,
            "transition_label": pt.transition_label,
        })

    xlsx_bytes = generate_excel(playlist.name, tracks_data)
    filename = f"{playlist.name.replace(' ', '_')}.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{playlist_id}/export/text")
async def export_text(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.export_service import generate_text

    result = await db.execute(
        select(Playlist)
        .options(selectinload(Playlist.playlist_tracks).selectinload(PlaylistTrack.track))
        .where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    pts = sorted(playlist.playlist_tracks, key=lambda pt: pt.position_scheduled or pt.position_original or 0)

    tracks_data = []
    for pt in pts:
        tracks_data.append({
            "position": pt.position_scheduled or pt.position_original,
            "title": pt.track.title,
            "artist": pt.track.artist,
            "key_camelot": pt.key_override or pt.track.key_camelot,
            "bpm": pt.bpm_override if pt.bpm_override is not None else pt.track.bpm,
            "energy": pt.energy_override if pt.energy_override is not None else pt.track.energy,
            "transition_score": pt.transition_score,
            "transition_label": pt.transition_label,
        })

    text = generate_text(playlist.name, tracks_data)
    return Response(content=text, media_type="text/plain")
