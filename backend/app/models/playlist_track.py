import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    playlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    position_original: Mapped[int | None] = mapped_column()
    position_scheduled: Mapped[int | None] = mapped_column()
    key_override: Mapped[str | None] = mapped_column(String(3))
    bpm_override: Mapped[Decimal | None] = mapped_column()
    energy_override: Mapped[int | None] = mapped_column()
    transition_score: Mapped[Decimal | None] = mapped_column()
    transition_label: Mapped[str | None] = mapped_column(String(20))

    playlist: Mapped["Playlist"] = relationship(back_populates="playlist_tracks")
    track: Mapped["Track"] = relationship()

    __table_args__ = (
        UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
    )
