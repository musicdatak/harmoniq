"""Tests for the Camelot engine — key parsing, scoring, compatibility."""

import pytest

from app.engine.camelot import (
    camelot_to_musical,
    classify_transition,
    get_compatible_keys,
    harmonic_score,
    musical_to_camelot,
    parse_key,
)


# ---- parse_key: 30+ inputs covering all formats ----

class TestParseKeyCamelot:
    """Direct Camelot codes."""

    def test_8a(self):
        assert parse_key("8A") == "8A"

    def test_11b(self):
        assert parse_key("11B") == "11B"

    def test_1a(self):
        assert parse_key("1A") == "1A"

    def test_12b(self):
        assert parse_key("12B") == "12B"

    def test_lowercase(self):
        assert parse_key("8a") == "8A"

    def test_with_spaces(self):
        assert parse_key("  11B  ") == "11B"


class TestParseKeyStandard:
    """Standard notation: 'A minor', 'F# major'."""

    def test_a_minor(self):
        assert parse_key("A minor") == "8A"

    def test_c_major(self):
        assert parse_key("C major") == "8B"

    def test_fsharp_major(self):
        assert parse_key("F# major") == "2B"

    def test_bb_minor(self):
        assert parse_key("Bb minor") == "3A"

    def test_ab_major(self):
        assert parse_key("Ab major") == "4B"

    def test_case_insensitive(self):
        assert parse_key("a MINOR") == "8A"

    def test_e_minor(self):
        assert parse_key("E minor") == "9A"

    def test_g_major(self):
        assert parse_key("G major") == "9B"

    def test_d_minor(self):
        assert parse_key("D minor") == "7A"


class TestParseKeyShorthand:
    """Shorthand: 'Am', 'F#m', 'Bb', 'C'."""

    def test_am(self):
        assert parse_key("Am") == "8A"

    def test_c(self):
        assert parse_key("C") == "8B"

    def test_fsharp_m(self):
        assert parse_key("F#m") == "11A"

    def test_bbm(self):
        assert parse_key("Bbm") == "3A"

    def test_db(self):
        assert parse_key("Db") == "3B"

    def test_em(self):
        assert parse_key("Em") == "9A"

    def test_g(self):
        assert parse_key("G") == "9B"


class TestParseKeySymbols:
    """Unicode symbols: F♯m, B♭."""

    def test_fsharp_symbol_m(self):
        assert parse_key("F♯m") == "11A"

    def test_bb_symbol(self):
        assert parse_key("B♭") == "6B"

    def test_ab_symbol_minor(self):
        assert parse_key("A♭ minor") == "1A"


class TestParseKeyFrench:
    """French notation."""

    def test_la_mineur(self):
        assert parse_key("La mineur") == "8A"

    def test_do_majeur(self):
        assert parse_key("Do majeur") == "8B"

    def test_si_bemol_majeur(self):
        assert parse_key("Si bémol majeur") == "6B"

    def test_re_mineur(self):
        assert parse_key("Ré mineur") == "7A"

    def test_sol_mineur(self):
        assert parse_key("Sol mineur") == "6A"

    def test_fa_diese_mineur(self):
        assert parse_key("Fa dièse mineur") == "11A"

    def test_mi_bemol_majeur(self):
        assert parse_key("Mi bémol majeur") == "5B"

    def test_case_insensitive_french(self):
        assert parse_key("la MINEUR") == "8A"


class TestParseKeyEnharmonic:
    """Enharmonic equivalents."""

    def test_gsharp_minor(self):
        assert parse_key("G#m") == "1A"

    def test_dsharp_minor(self):
        assert parse_key("D#m") == "2A"

    def test_asharp_minor(self):
        assert parse_key("A#m") == "3A"

    def test_csharp_major(self):
        assert parse_key("C#") == "3B"

    def test_gb_major(self):
        assert parse_key("Gb") == "2B"


class TestParseKeyEdgeCases:
    def test_none_input(self):
        assert parse_key("") is None

    def test_garbage(self):
        assert parse_key("not a key") is None

    def test_invalid_camelot(self):
        assert parse_key("13A") is None

    def test_whitespace_only(self):
        assert parse_key("   ") is None


# ---- harmonic_score ----

class TestHarmonicScore:
    def test_same_key(self):
        assert harmonic_score("8A", "8A") == 100

    def test_switch_ab(self):
        """Same number, different letter = 85."""
        assert harmonic_score("8A", "8B") == 85

    def test_plus_one_same_letter(self):
        assert harmonic_score("8A", "9A") == 85

    def test_minus_one_same_letter(self):
        assert harmonic_score("8A", "7A") == 85

    def test_wrap_around_12_to_1(self):
        """12A → 1A should be distance 1 = 85."""
        assert harmonic_score("12A", "1A") == 85

    def test_plus_two_same_letter(self):
        assert harmonic_score("8A", "10A") == 55

    def test_plus_one_different_letter(self):
        assert harmonic_score("8A", "9B") == 50

    def test_clash_far_apart(self):
        assert harmonic_score("8A", "2B") == 10

    def test_clash_opposite(self):
        assert harmonic_score("1A", "7A") == 10

    def test_symmetry(self):
        assert harmonic_score("5A", "6A") == harmonic_score("6A", "5A")


# ---- get_compatible_keys ----

class TestGetCompatibleKeys:
    def test_8a_compatible(self):
        keys = get_compatible_keys("8A")
        assert "8A" in keys
        assert "8B" in keys
        assert "9A" in keys
        assert "7A" in keys
        assert len(keys) == 4

    def test_1a_wraps(self):
        keys = get_compatible_keys("1A")
        assert "12A" in keys
        assert "2A" in keys

    def test_12b_wraps(self):
        keys = get_compatible_keys("12B")
        assert "1B" in keys
        assert "11B" in keys


# ---- classify_transition ----

class TestClassifyTransition:
    def test_perfect(self):
        assert classify_transition("8A", "8A") == "Perfect"

    def test_harmonic(self):
        assert classify_transition("8A", "8B") == "Harmonic"
        assert classify_transition("8A", "9A") == "Harmonic"

    def test_near(self):
        assert classify_transition("8A", "10A") == "Near"
        assert classify_transition("8A", "9B") == "Near"

    def test_clash(self):
        assert classify_transition("8A", "2A") == "Clash"


# ---- musical_to_camelot ----

class TestMusicalToCamelot:
    def test_a_minor(self):
        assert musical_to_camelot("A", "minor") == "8A"

    def test_c_major(self):
        assert musical_to_camelot("C", "major") == "8B"

    def test_ab_minor(self):
        assert musical_to_camelot("Ab", "minor") == "1A"

    def test_fsharp_major(self):
        assert musical_to_camelot("F#", "major") == "2B"


# ---- camelot_to_musical ----

class TestCamelotToMusical:
    def test_8a(self):
        assert camelot_to_musical("8A") == "A minor"

    def test_8b(self):
        assert camelot_to_musical("8B") == "C major"

    def test_invalid(self):
        assert camelot_to_musical("99X") is None
