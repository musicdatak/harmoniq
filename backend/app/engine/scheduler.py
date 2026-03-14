"""Scheduling engine — transition scoring and greedy playlist sequencing."""

from dataclasses import dataclass
from decimal import Decimal

from app.engine.camelot import classify_transition, harmonic_score


@dataclass
class TrackData:
    """Lightweight track representation for the scheduler."""
    id: str
    title: str
    artist: str
    camelot: str | None = None
    bpm: float | None = None
    energy: float | None = None


def transition_score(
    track_a: TrackData,
    track_b: TrackData,
    weights: dict[str, int],
    position_ratio: float | None = None,
) -> float:
    """Score a transition between two tracks (0-100)."""
    total_weight = weights["harmony"] + weights["energy"] + weights["bpm"]
    if total_weight == 0:
        return 50.0

    # Harmonic score
    if track_a.camelot and track_b.camelot:
        h_score = harmonic_score(track_a.camelot, track_b.camelot)
    else:
        h_score = 50

    # Energy score
    if track_a.energy is not None and track_b.energy is not None:
        if position_ratio is not None:
            # Energy arc mode
            if position_ratio <= 0.65:
                target = 2 + 8 * (position_ratio / 0.65)
            else:
                target = 10 - 7 * ((position_ratio - 0.65) / 0.35)
            e_score = max(0, 100 - abs(track_b.energy - target) * 15)
        else:
            e_score = max(0, 100 - abs(track_a.energy - track_b.energy) * 15)
    else:
        e_score = 50

    # BPM score
    if track_a.bpm is not None and track_b.bpm is not None:
        b_score = max(0, 100 - abs(track_a.bpm - track_b.bpm) * 2)
    else:
        b_score = 50

    return (
        weights["harmony"] * h_score
        + weights["energy"] * e_score
        + weights["bpm"] * b_score
    ) / total_weight


def schedule_playlist(
    tracks: list[TrackData],
    weights: dict[str, int],
    energy_arc: bool = False,
) -> list[TrackData]:
    """Greedy nearest-neighbor scheduling for harmonic flow."""
    if len(tracks) <= 1:
        return list(tracks)

    remaining = list(tracks)
    scheduled: list[TrackData] = []

    # Pick best starting track (highest average compatibility with all others)
    best_start = max(
        range(len(remaining)),
        key=lambda i: sum(
            transition_score(remaining[i], remaining[j], weights)
            for j in range(len(remaining))
            if j != i
        ) / (len(remaining) - 1),
    )
    scheduled.append(remaining.pop(best_start))

    # Greedily pick the best next track
    while remaining:
        last = scheduled[-1]
        pos_ratio = len(scheduled) / (len(scheduled) + len(remaining)) if energy_arc else None
        best_idx = max(
            range(len(remaining)),
            key=lambda i: transition_score(last, remaining[i], weights, pos_ratio),
        )
        scheduled.append(remaining.pop(best_idx))

    return scheduled
