"""Camelot Wheel engine — key parsing, harmonic scoring, compatibility."""

import re

# All 24 keys: (camelot_code, musical_key, color)
CAMELOT_DATA = [
    ("1A", "Ab minor", "#FF6B6B"),
    ("1B", "B major", "#FF6B6B"),
    ("2A", "Eb minor", "#FF8E53"),
    ("2B", "F# major", "#FF8E53"),
    ("3A", "Bb minor", "#FFB347"),
    ("3B", "Db major", "#FFB347"),
    ("4A", "F minor", "#FFD93D"),
    ("4B", "Ab major", "#FFD93D"),
    ("5A", "C minor", "#6BCB77"),
    ("5B", "Eb major", "#6BCB77"),
    ("6A", "G minor", "#4D96FF"),
    ("6B", "Bb major", "#4D96FF"),
    ("7A", "D minor", "#6B5CE7"),
    ("7B", "F major", "#6B5CE7"),
    ("8A", "A minor", "#9B59B6"),
    ("8B", "C major", "#9B59B6"),
    ("9A", "E minor", "#E056A0"),
    ("9B", "G major", "#E056A0"),
    ("10A", "B minor", "#FF4757"),
    ("10B", "D major", "#FF4757"),
    ("11A", "F# minor", "#1ABC9C"),
    ("11B", "A major", "#1ABC9C"),
    ("12A", "Db minor", "#3498DB"),
    ("12B", "E major", "#3498DB"),
]

# Lookup maps
_code_to_musical: dict[str, str] = {}
_code_to_color: dict[str, str] = {}
_musical_to_code: dict[str, str] = {}

for _code, _musical, _color in CAMELOT_DATA:
    _code_to_musical[_code] = _musical
    _code_to_color[_code] = _color
    _musical_to_code[_musical.lower()] = _code

# --- Note name normalization ---

# Map standard note names to canonical form
_NOTE_CANONICAL = {
    "c": "C", "d": "D", "e": "E", "f": "F", "g": "G", "a": "A", "b": "B",
}

# Accidental normalization
_ACCIDENTAL_MAP = {
    "#": "#", "♯": "#", "sharp": "#",
    "b": "b", "♭": "b", "flat": "b",
    "bb": "bb", "𝄫": "bb",
}

# French note names → English
_FRENCH_NOTES = {
    "do": "C", "ré": "D", "re": "D", "mi": "E", "fa": "F",
    "sol": "G", "la": "A", "si": "B",
}

# French accidentals
_FRENCH_ACCIDENTALS = {
    "dièse": "#", "dieze": "#", "diese": "#",
    "bémol": "b", "bemol": "b",
}

# French scale words
_FRENCH_SCALES = {
    "majeur": "major", "mineur": "minor",
}

# All musical keys mapped to Camelot (using enharmonic equivalents)
_KEY_TO_CAMELOT: dict[str, str] = {}

# Build from CAMELOT_DATA
for _code, _musical, _ in CAMELOT_DATA:
    parts = _musical.split()
    note = parts[0]
    scale = parts[1]
    _KEY_TO_CAMELOT[(note.lower(), scale.lower())] = _code

# Enharmonic equivalents
_ENHARMONICS = {
    "G#": "Ab", "D#": "Eb", "A#": "Bb",
    "Gb": "F#", "C#": "Db",
    "G#m": "Abm", "D#m": "Ebm", "A#m": "Bbm",
    "Gbm": "F#m", "C#m": "Dbm",
}

# Add enharmonic mappings
_ENHARMONIC_NOTE_MAP = {
    "g#": "ab", "d#": "eb", "a#": "bb",
    "gb": "f#", "c#": "db",
    "cb": "b", "fb": "e", "e#": "f", "b#": "c",
}


def _parse_camelot_direct(s: str) -> str | None:
    """Try to parse as Camelot code like '8A', '11B'."""
    m = re.match(r'^(\d{1,2})([AaBb])$', s.strip())
    if m:
        num = int(m.group(1))
        letter = m.group(2).upper()
        code = f"{num}{letter}"
        if code in _code_to_musical:
            return code
    return None


def _normalize_note_and_scale(note: str, accidental: str, scale: str) -> str | None:
    """Given a parsed note, accidental, and scale, return Camelot code or None."""
    # Build the full note name
    full_note = note.capitalize() + accidental  # e.g. "Ab", "F#", "C"

    # Handle enharmonics
    if full_note.lower() in _ENHARMONIC_NOTE_MAP:
        full_note_lookup = _ENHARMONIC_NOTE_MAP[full_note.lower()]
    else:
        full_note_lookup = full_note.lower()

    scale_lower = scale.lower()
    key = (full_note_lookup, scale_lower)
    if key in _KEY_TO_CAMELOT:
        return _KEY_TO_CAMELOT[key]
    return None


def _parse_french(s: str) -> str | None:
    """Parse French key names like 'La mineur', 'Si bémol majeur', 'Fa dièse mineur'."""
    s_lower = s.strip().lower()

    # Try pattern: <french_note> [<french_accidental>] <french_scale>
    # Split into words
    words = s_lower.split()
    if len(words) < 2:
        return None

    # First word must be a French note
    if words[0] not in _FRENCH_NOTES:
        return None

    note = _FRENCH_NOTES[words[0]]
    accidental = ""
    scale = None

    if len(words) == 2:
        # "La mineur" or "Do majeur"
        if words[1] in _FRENCH_SCALES:
            scale = _FRENCH_SCALES[words[1]]
    elif len(words) == 3:
        # "Si bémol majeur" or "Fa dièse mineur"
        if words[1] in _FRENCH_ACCIDENTALS and words[2] in _FRENCH_SCALES:
            accidental = _FRENCH_ACCIDENTALS[words[1]]
            scale = _FRENCH_SCALES[words[2]]

    if scale is None:
        return None

    return _normalize_note_and_scale(note, accidental, scale)


def _parse_standard(s: str) -> str | None:
    """Parse standard notation: 'A minor', 'F# major', 'Bb minor', 'Ab major'."""
    s = s.strip()
    # Pattern: note [accidental] (minor|major)
    m = re.match(
        r'^([A-Ga-g])\s*([#♯b♭]?)\s*(minor|major|min|maj)$',
        s, re.IGNORECASE,
    )
    if m:
        note = m.group(1)
        acc = m.group(2)
        scale_raw = m.group(3).lower()
        # Normalize accidental
        if acc in ("♯",):
            acc = "#"
        elif acc in ("♭",):
            acc = "b"
        # Normalize scale
        scale = "minor" if scale_raw in ("minor", "min") else "major"
        return _normalize_note_and_scale(note, acc, scale)
    return None


def _parse_shorthand(s: str) -> str | None:
    """Parse shorthand: 'Am', 'F#m', 'Bbm', 'C', 'Db', 'F#'."""
    s = s.strip()
    # Minor shorthand: note + optional accidental + 'm'
    m = re.match(r'^([A-Ga-g])\s*([#♯b♭]?)\s*m$', s, re.IGNORECASE)
    if m:
        note = m.group(1)
        acc = m.group(2)
        if acc in ("♯",):
            acc = "#"
        elif acc in ("♭",):
            acc = "b"
        return _normalize_note_and_scale(note, acc, "minor")

    # Major shorthand: just note + optional accidental (no 'm')
    m = re.match(r'^([A-Ga-g])\s*([#♯b♭]?)$', s, re.IGNORECASE)
    if m:
        note = m.group(1)
        acc = m.group(2)
        if acc in ("♯",):
            acc = "#"
        elif acc in ("♭",):
            acc = "b"
        return _normalize_note_and_scale(note, acc, "major")

    return None


def parse_key(input_str: str) -> str | None:
    """Parse any key format and return Camelot code, or None if unrecognized.

    Accepts: Camelot ("8A"), standard ("A minor"), shorthand ("Am"),
    symbols ("F♯m"), French ("La mineur", "Fa dièse mineur").
    Case-insensitive, whitespace-tolerant.
    """
    if not input_str or not input_str.strip():
        return None

    s = input_str.strip()

    # 1. Try Camelot direct
    result = _parse_camelot_direct(s)
    if result:
        return result

    # 2. Try French
    result = _parse_french(s)
    if result:
        return result

    # 3. Try standard notation
    result = _parse_standard(s)
    if result:
        return result

    # 4. Try shorthand
    result = _parse_shorthand(s)
    if result:
        return result

    return None


def harmonic_score(from_code: str, to_code: str) -> int:
    """Score harmonic compatibility between two Camelot codes (0-100)."""
    if from_code == to_code:
        return 100

    from_num = int(from_code[:-1])
    from_letter = from_code[-1]
    to_num = int(to_code[:-1])
    to_letter = to_code[-1]

    distance = min(abs(from_num - to_num), 12 - abs(from_num - to_num))

    if distance == 0 and from_letter != to_letter:
        return 85  # Same number, switch A↔B
    if distance == 1 and from_letter == to_letter:
        return 85  # Adjacent, same letter
    if distance == 2 and from_letter == to_letter:
        return 55  # Two steps, same letter
    if distance == 1 and from_letter != to_letter:
        return 50  # Adjacent, different letter

    return 10  # Clash


def get_compatible_keys(code: str) -> list[str]:
    """Return list of 4 compatible Camelot codes (score >= 85)."""
    num = int(code[:-1])
    letter = code[-1]
    other_letter = "B" if letter == "A" else "A"

    # Same code excluded (it's identity, not a "compatible" transition)
    results = []
    # Same number, other letter
    results.append(f"{num}{other_letter}")
    # +1 same letter
    next_num = (num % 12) + 1
    results.append(f"{next_num}{letter}")
    # -1 same letter
    prev_num = ((num - 2) % 12) + 1
    results.append(f"{prev_num}{letter}")
    # The code itself for completeness? No — return the 3 compatible + itself is 4
    # Actually let's return: same-num-switch, +1, -1 (3 transitions scoring 85)
    # But spec says "list of 4 compatible codes" — include self
    results.insert(0, code)

    return results


def classify_transition(from_code: str, to_code: str) -> str:
    """Classify a transition: Perfect/Harmonic/Near/Clash."""
    score = harmonic_score(from_code, to_code)
    if score == 100:
        return "Perfect"
    if score == 85:
        return "Harmonic"
    if score >= 50:
        return "Near"
    return "Clash"


def musical_to_camelot(key: str, scale: str) -> str | None:
    """Convert Essentia output (key='A', scale='minor') to Camelot code."""
    result = _normalize_note_and_scale(key, "", scale)
    if result:
        return result
    # Try with the key as-is (might contain accidental like 'Ab')
    if len(key) > 1:
        note = key[0]
        acc = key[1:]
        return _normalize_note_and_scale(note, acc, scale)
    return None


def camelot_to_musical(code: str) -> str | None:
    """Convert Camelot code to readable musical key name."""
    return _code_to_musical.get(code)


def get_color(code: str) -> str | None:
    """Get the color for a Camelot code."""
    return _code_to_color.get(code)
