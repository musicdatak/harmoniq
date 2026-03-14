"""Track override endpoint."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.playlist import Playlist
from app.models.playlist_track import PlaylistTrack
from app.models.user import User
from app.schemas.playlist import PlaylistTrackResponse, TrackOverrideUpdate
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/playlists", tags=["tracks"])


@router.put("/{playlist_id}/tracks/{track_id}", response_model=PlaylistTrackResponse)
async def update_track_override(
    playlist_id: uuid.UUID,
    track_id: uuid.UUID,
    body: TrackOverrideUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify playlist ownership
    pl_result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == current_user.id)
    )
    if not pl_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Find playlist_track
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(PlaylistTrack)
        .options(selectinload(PlaylistTrack.track))
        .where(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id)
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Track not in playlist")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pt, field, value)

    await db.commit()
    await db.refresh(pt)
    return pt
