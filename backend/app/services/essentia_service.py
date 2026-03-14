"""Server-side audio analysis using Essentia."""

import logging

from app.engine.camelot import musical_to_camelot

logger = logging.getLogger(__name__)


class EssentiaAnalyzer:
    """Analyze audio files for key, BPM, energy, loudness, danceability."""

    def analyze_file(self, filepath: str) -> dict:
        """Analyze an audio file and return musical features.

        Returns dict with key_musical, key_camelot, key_confidence,
        bpm, energy, loudness, danceability.

        Raises RuntimeError on analysis failure.
        """
        try:
            import essentia.standard as es
        except ImportError:
            raise RuntimeError("Essentia is not installed")

        try:
            audio = es.MonoLoader(filename=filepath, sampleRate=44100)()
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {e}")

        if len(audio) < 44100:  # Less than 1 second
            raise RuntimeError("Audio file too short for analysis")

        try:
            key, scale, key_strength = es.KeyExtractor()(audio)
        except Exception:
            key, scale, key_strength = None, None, 0.0

        try:
            bpm, beats, beats_confidence, _, _ = es.RhythmExtractor2013(
                method="multifeature"
            )(audio)
        except Exception:
            bpm, beats_confidence = 0.0, 0.0

        try:
            energy = es.Energy()(audio)
        except Exception:
            energy = 0.0

        try:
            loudness = es.Loudness()(audio)
        except Exception:
            loudness = 0.0

        try:
            danceability_val, _ = es.Danceability()(audio)
        except Exception:
            danceability_val = 0.0

        # Build key info
        key_musical = f"{key} {scale}" if key and scale else None
        key_camelot = musical_to_camelot(key, scale) if key and scale else None

        # Normalize energy to 0-10 scale (raw Essentia energy is unbounded)
        # Use log scale: log10(energy+1) capped at 10
        import math
        energy_normalized = min(10.0, math.log10(float(energy) + 1) * 2) if energy else 0.0

        # Normalize danceability to 0-1 range (raw values can be large)
        dance_normalized = min(1.0, float(danceability_val) / 3.0) if danceability_val else 0.0

        # Cap loudness to fit NUMERIC(6,2) = max 9999.99
        loudness_capped = max(-9999.99, min(9999.99, float(loudness))) if loudness else 0.0

        return {
            "key_musical": key_musical,
            "key_camelot": key_camelot,
            "key_confidence": round(float(key_strength), 3) if key_strength else None,
            "bpm": round(float(bpm), 2) if bpm else None,
            "energy": round(energy_normalized, 2),
            "loudness": round(loudness_capped, 2),
            "danceability": round(dance_normalized, 3),
        }


# Module-level singleton
analyzer = EssentiaAnalyzer()
