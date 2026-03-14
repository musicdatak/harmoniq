"""Audio analysis endpoints — server-side Essentia + browser results."""

import os
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.models.track import Track
from app.models.user import User
from app.schemas.playlist import TrackResponse
from app.services.auth_service import get_current_user
from app.services.essentia_service import analyzer

router = APIRouter(prefix="/api", tags=["analysis"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class BrowserAnalysisResult(BaseModel):
    bpm: float | None = None
    energy: float | None = None
    key_musical: str | None = None
    key_camelot: str | None = None
    key_confidence: float | None = None
    loudness: float | None = None
    danceability: float | None = None


async def _analyze_and_update(track: Track, filepath: str, db: AsyncSession) -> Track:
    """Run Essentia analysis on a file and update the track."""
    try:
        result = analyzer.analyze_file(filepath)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    track.key_musical = result["key_musical"]
    track.key_camelot = result["key_camelot"]
    track.key_confidence = result["key_confidence"]
    track.bpm = result["bpm"]
    track.energy = result["energy"]
    track.loudness = result["loudness"]
    track.danceability = result["danceability"]
    track.analysis_source = "essentia_server"
    track.enrichment_status = "analyzed"
    track.enriched_at = datetime.utcnow()

    await db.commit()
    await db.refresh(track)
    return track


@router.post("/tracks/{track_id}/analyze", response_model=TrackResponse)
async def analyze_track(
    track_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a single audio file for server-side Essentia analysis."""
    # Verify track exists
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # Validate file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Save to temp file, analyze, delete
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        track = await _analyze_and_update(track, tmp_path, db)
    finally:
        os.unlink(tmp_path)

    return track


@router.post("/playlists/{playlist_id}/analyze-batch")
async def analyze_batch(
    playlist_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload multiple audio files, match to tracks by filename, analyze each."""
    # Verify playlist ownership
    pl_result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not pl_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Load playlist tracks
    result = await db.execute(
        select(PlaylistTrack)
        .options(selectinload(PlaylistTrack.track))
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    pts = result.scalars().all()

    # Build lookup: lowercase title/artist fragments → track
    track_lookup: dict[str, Track] = {}
    for pt in pts:
        t = pt.track
        # Match by title, artist, or "artist - title"
        track_lookup[t.title.lower()] = t
        track_lookup[t.artist.lower()] = t
        track_lookup[f"{t.artist} - {t.title}".lower()] = t
        track_lookup[f"{t.artist.lower()}_{t.title.lower()}"] = t

    results = []
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({"filename": file.filename, "status": "skipped", "reason": "unsupported format"})
            continue

        # Try to match filename to a track
        basename = os.path.splitext(file.filename or "")[0].lower().strip()
        # Try various matching strategies
        matched_track = None
        for key in [basename, basename.replace("_", " "), basename.replace("-", " ")]:
            if key in track_lookup:
                matched_track = track_lookup[key]
                break

        # Fuzzy: check if filename contains track title or artist
        if not matched_track:
            for pt in pts:
                t = pt.track
                if t.title.lower() in basename or t.artist.lower() in basename:
                    matched_track = t
                    break

        if not matched_track:
            results.append({"filename": file.filename, "status": "skipped", "reason": "no matching track"})
            continue

        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            results.append({"filename": file.filename, "status": "skipped", "reason": "too large"})
            continue

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            await _analyze_and_update(matched_track, tmp_path, db)
            results.append({
                "filename": file.filename,
                "status": "analyzed",
                "track": f"{matched_track.artist} - {matched_track.title}",
                "key_camelot": matched_track.key_camelot,
                "bpm": float(matched_track.bpm) if matched_track.bpm else None,
            })
        except HTTPException as e:
            results.append({"filename": file.filename, "status": "error", "reason": e.detail})
        finally:
            os.unlink(tmp_path)

    return {"results": results}


@router.put("/tracks/{track_id}/update-analysis", response_model=TrackResponse)
async def update_analysis(
    track_id: uuid.UUID,
    body: BrowserAnalysisResult,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Receive browser-side (Essentia.js) analysis results and update track."""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    if body.bpm is not None:
        track.bpm = body.bpm
    if body.energy is not None:
        track.energy = body.energy
    if body.key_musical is not None:
        track.key_musical = body.key_musical
    if body.key_camelot is not None:
        track.key_camelot = body.key_camelot
    if body.key_confidence is not None:
        track.key_confidence = body.key_confidence
    if body.loudness is not None:
        track.loudness = body.loudness
    if body.danceability is not None:
        track.danceability = body.danceability

    track.analysis_source = "essentia_browser"
    track.enrichment_status = "analyzed"
    track.enriched_at = datetime.utcnow()

    await db.commit()
    await db.refresh(track)
    return track
