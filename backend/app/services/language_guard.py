"""Conservative script/lexical guard for the English-first baseline.

This is not a general language detector. It identifies non-Latin script and a
small set of distinctive Romanized-Hindi markers so the current baseline can
abstain instead of presenting an unsupported-language prediction as reliable.
"""

import re
import unicodedata

HINGLISH_MARKERS = {
    "aap",
    "aapka",
    "aapki",
    "aapko",
    "abhi",
    "apka",
    "apki",
    "apko",
    "band",
    "bheje",
    "bhejo",
    "dhanyavad",
    "hai",
    "hain",
    "karein",
    "karna",
    "karo",
    "khata",
    "khate",
    "kripya",
    "kyu",
    "kya",
    "kyun",
    "mat",
    "nahi",
    "nahin",
    "paisa",
    "paise",
    "rupaye",
    "turant",
    "bhejna",
}


def inspect_language_support(text):
    """Return script/lexical signals without claiming exact language identity."""
    cleaned = (text or "").strip()
    latin_letters = []
    non_latin_letters = []

    for character in cleaned:
        if not character.isalpha():
            continue
        unicode_name = unicodedata.name(character, "")
        if unicode_name.startswith("LATIN"):
            latin_letters.append(character)
        else:
            non_latin_letters.append(character)

    if latin_letters and non_latin_letters:
        script_profile = "mixed_latin_non_latin"
    elif non_latin_letters:
        script_profile = "non_latin"
    else:
        script_profile = "latin"

    tokens = set(re.findall(r"[a-z]+", cleaned.casefold()))
    markers = sorted(tokens.intersection(HINGLISH_MARKERS))

    has_unsupported_script = bool(non_latin_letters)
    has_romanized_hindi_signal = bool(markers)
    baseline_eligible = not has_unsupported_script and not has_romanized_hindi_signal

    return {
        "script_profile": script_profile,
        "romanized_hindi_markers": markers,
        "baseline_eligible": baseline_eligible,
        "coverage_status": (
            "unvalidated_latin_text"
            if baseline_eligible
            else "unvalidated_non_english_or_mixed_language"
        ),
        "coverage_note": (
            "Latin script alone does not prove that a message is English or that "
            "this model is calibrated for its language."
            if baseline_eligible
            else "The current baseline has not been validated for this script or "
            "Romanized-Hindi signal; the classifier abstained."
        ),
    }
