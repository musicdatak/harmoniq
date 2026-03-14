"""Tests for the scheduling engine."""

import pytest

from app.engine.camelot import harmonic_score
from app.engine.scheduler import TrackData, schedule_playlist, transition_score


def _make_track(title: str, camelot: str | None = None, bpm: float | None = None, energy: float | None = None) -> TrackData:
    return TrackData(id=title, title=title, artist="Test", camelot=camelot, bpm=bpm, energy=energy)


DEFAULT_WEIGHTS = {"harmony": 80, "energy": 50, "bpm": 30}


class TestTransitionScore:
    def test_same_key_same_bpm_same_energy(self):
        a = _make_track("A", "8A", 120.0, 5.0)
        b = _make_track("B", "8A", 120.0, 5.0)
        score = transition_score(a, b, DEFAULT_WEIGHTS)
        assert score == 100.0

    def test_missing_data_defaults_to_50(self):
        a = _make_track("A")
        b = _make_track("B")
        score = transition_score(a, b, DEFAULT_WEIGHTS)
        assert score == 50.0

    def test_zero_weights_returns_50(self):
        a = _make_track("A", "8A", 120.0, 5.0)
        b = _make_track("B", "1A", 60.0, 10.0)
        score = transition_score(a, b, {"harmony": 0, "energy": 0, "bpm": 0})
        assert score == 50.0

    def test_harmony_dominant(self):
        """With high harmony weight, harmonically compatible tracks score higher."""
        a = _make_track("A", "8A", 120.0, 5.0)
        b_good = _make_track("B", "9A", 120.0, 5.0)  # harmonic
        b_bad = _make_track("C", "2A", 120.0, 5.0)   # clash
        weights = {"harmony": 100, "energy": 0, "bpm": 0}
        assert transition_score(a, b_good, weights) > transition_score(a, b_bad, weights)


class TestSchedulePlaylist:
    def test_empty(self):
        assert schedule_playlist([], DEFAULT_WEIGHTS) == []

    def test_single_track(self):
        t = _make_track("A", "8A")
        result = schedule_playlist([t], DEFAULT_WEIGHTS)
        assert len(result) == 1
        assert result[0].id == "A"

    def test_10_tracks_all_present(self):
        """Schedule 10 tracks and verify all are included."""
        tracks = [
            _make_track("T1", "8A", 120, 5),
            _make_track("T2", "9A", 122, 6),
            _make_track("T3", "8B", 118, 4),
            _make_track("T4", "7A", 125, 7),
            _make_track("T5", "10A", 115, 3),
            _make_track("T6", "6A", 130, 8),
            _make_track("T7", "5B", 119, 5),
            _make_track("T8", "8A", 121, 6),
            _make_track("T9", "9B", 117, 4),
            _make_track("T10", "11A", 128, 7),
        ]
        result = schedule_playlist(tracks, DEFAULT_WEIGHTS)
        assert len(result) == 10
        assert set(t.id for t in result) == set(t.id for t in tracks)

    def test_10_tracks_harmonic_flow(self):
        """Verify consecutive tracks tend to be harmonically compatible."""
        tracks = [
            _make_track("T1", "8A", 120, 5),
            _make_track("T2", "9A", 122, 6),
            _make_track("T3", "8B", 118, 4),
            _make_track("T4", "2A", 125, 7),  # clash with 8A
            _make_track("T5", "10A", 115, 3),
            _make_track("T6", "3A", 130, 8),  # clash with 8A
            _make_track("T7", "5B", 119, 5),
            _make_track("T8", "8A", 121, 6),
            _make_track("T9", "9B", 117, 4),
            _make_track("T10", "7A", 128, 7),
        ]
        weights = {"harmony": 100, "energy": 0, "bpm": 0}
        result = schedule_playlist(tracks, weights)

        # Count harmonic transitions (score >= 50)
        good_transitions = 0
        for i in range(len(result) - 1):
            if result[i].camelot and result[i + 1].camelot:
                score = harmonic_score(result[i].camelot, result[i + 1].camelot)
                if score >= 50:
                    good_transitions += 1

        # With a harmony-focused scheduler, most transitions should be decent
        assert good_transitions >= 5, f"Only {good_transitions}/9 good transitions"

    def test_energy_arc_rising_then_falling(self):
        """With energy arc, tracks should build up then wind down."""
        tracks = [
            _make_track("Low1", "8A", 120, 1.0),
            _make_track("Low2", "8A", 120, 2.0),
            _make_track("Mid1", "8A", 120, 5.0),
            _make_track("Mid2", "8A", 120, 6.0),
            _make_track("High1", "8A", 120, 9.0),
            _make_track("High2", "8A", 120, 10.0),
            _make_track("Wind1", "8A", 120, 4.0),
            _make_track("Wind2", "8A", 120, 3.0),
        ]
        # All same key/BPM so only energy matters
        weights = {"harmony": 0, "energy": 100, "bpm": 0}
        result = schedule_playlist(tracks, weights, energy_arc=True)

        energies = [t.energy for t in result]

        # The peak energy should be roughly in the first 65% of the playlist
        peak_idx = energies.index(max(energies))
        peak_ratio = peak_idx / (len(energies) - 1)
        # Allow some tolerance — peak should be in first 80%
        assert peak_ratio <= 0.85, f"Peak at position {peak_idx}/{len(energies)-1} = {peak_ratio:.2f}"

        # Energy at the end should be lower than the peak
        assert energies[-1] < max(energies), "Last track should not be the peak"
