import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    artist: Mapped[str] = mapped_column(String(500), nullable=False)
    musicbrainz_id: Mapped[str | None] = mapped_column(String(255))
    key_musical: Mapped[str | None] = mapped_column(String(50))
    key_camelot: Mapped[str | None] = mapped_column(String(3))
    key_confidence: Mapped[Decimal | None] = mapped_column()
    bpm: Mapped[Decimal | None] = mapped_column()
    bpm_confidence: Mapped[Decimal | None] = mapped_column()
    energy: Mapped[Decimal | None] = mapped_column()
    loudness: Mapped[Decimal | None] = mapped_column()
    danceability: Mapped[Decimal | None] = mapped_column()
    genre: Mapped[str | None] = mapped_column(String(255))
    analysis_source: Mapped[str | None] = mapped_column(String(20))
    enrichment_status: Mapped[str] = mapped_column(String(20), default="pending")
    enriched_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tracks_title_artist_unique", func.lower(title), func.lower(artist), unique=True),
    )
