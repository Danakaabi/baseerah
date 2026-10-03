from app.ingestion.text import normalize_arabic


def test_normalize_arabic_removes_diacritics() -> None:
    text = "إِنَّمَا الأَعْمَالُ"

    result = normalize_arabic(text)

    assert result == "انما الاعمال"


def test_normalize_arabic_removes_tatweel() -> None:
    text = "بصيــــرة"

    result = normalize_arabic(text)

    assert result == "بصيرة"


def test_normalize_arabic_preserves_paragraphs() -> None:
    text = "النص الأول.\n\nالنص الثاني."

    result = normalize_arabic(text)

    assert "\n\n" in result