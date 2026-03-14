"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "tracks",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("artist", sa.String(500), nullable=False),
        sa.Column("musicbrainz_id", sa.String(255), nullable=True),
        sa.Column("key_musical", sa.String(50), nullable=True),
        sa.Column("key_camelot", sa.String(3), nullable=True),
        sa.Column("key_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("bpm", sa.Numeric(6, 2), nullable=True),
        sa.Column("bpm_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("energy", sa.Numeric(4, 2), nullable=True),
        sa.Column("loudness", sa.Numeric(6, 2), nullable=True),
        sa.Column("danceability", sa.Numeric(4, 3), nullable=True),
        sa.Column("genre", sa.String(255), nullable=True),
        sa.Column("analysis_source", sa.String(20), nullable=True),
        sa.Column("enrichment_status", sa.String(20), server_default="pending", nullable=True),
        sa.Column("enriched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tracks_title_artist_unique",
        "tracks",
        [sa.text("lower(title)"), sa.text("lower(artist)")],
        unique=True,
    )

    op.create_table(
        "playlists",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("harmony_weight", sa.Integer(), server_default="80", nullable=True),
        sa.Column("energy_weight", sa.Integer(), server_default="50", nullable=True),
        sa.Column("bpm_weight", sa.Integer(), server_default="30", nullable=True),
        sa.Column("energy_arc_mode", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("mix_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_scheduled", sa.Boolean(), server_default="false", nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "playlist_tracks",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("position_original", sa.Integer(), nullable=True),
        sa.Column("position_scheduled", sa.Integer(), nullable=True),
        sa.Column("key_override", sa.String(3), nullable=True),
        sa.Column("bpm_override", sa.Numeric(6, 2), nullable=True),
        sa.Column("energy_override", sa.Integer(), nullable=True),
        sa.Column("transition_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("transition_label", sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("playlist_id", "track_id", name="uq_playlist_track"),
    )


def downgrade() -> None:
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
    op.drop_index("ix_tracks_title_artist_unique", table_name="tracks")
    op.drop_table("tracks")
    op.drop_table("users")
