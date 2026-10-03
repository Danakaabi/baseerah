import re
import unicodedata


# Arabic diacritics only.
# Important: keep the regex compact so whitespace/newlines
# are never accidentally treated as removable characters.
_ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

_HORIZONTAL_WHITESPACE = re.compile(r"[ \t]+")
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for retrieval while preserving
    paragraph boundaries and readable source content.

    Operations:
    - Unicode normalization
    - remove tatweel
    - remove Arabic diacritics
    - normalize Alef variants
    - normalize horizontal whitespace
    - preserve paragraph boundaries

    The function intentionally avoids aggressive transformations
    such as converting Ta Marbuta or Alef Maqsura.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    # Normalize Unicode representation.
    text = unicodedata.normalize("NFKC", text)

    # Normalize Windows/macOS line endings first.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove Arabic tatweel.
    text = text.replace("\u0640", "")

    # Remove Arabic diacritics.
    text = _ARABIC_DIACRITICS.sub("", text)

    # Normalize common Alef variants.
    text = re.sub(r"[إأآٱ]", "ا", text)

    # Normalize spaces/tabs WITHOUT touching newlines.
    text = _HORIZONTAL_WHITESPACE.sub(" ", text)

    # Remove unnecessary spaces around individual lines,
    # while preserving empty lines between paragraphs.
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Three or more newlines become exactly two.
    text = _MULTIPLE_NEWLINES.sub("\n\n", text)

    return text.strip()