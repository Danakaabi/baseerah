import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "demo"
    / "hadeethenc"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)


def load_record(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_source_document(
    record: dict,
) -> dict:
    hadith_id = record["hadith_id"]

    hadith_text = (
        record.get("text") or ""
    ).strip()

    explanation = (
        record.get("explanation") or ""
    ).strip()

    if not hadith_text:
        raise ValueError(
            f"Hadith {hadith_id} has no text"
        )

    text_parts = [
        hadith_text,
    ]

    if explanation:
        text_parts.append(explanation)

    combined_text = "\n\n".join(
        text_parts
    )

    return {
        "source_id": (
            f"hadeethenc-{hadith_id}"
        ),
        "source_name": (
            "موسوعة الأحاديث النبوية - HadeethEnc"
        ),
        "source_url": record["source_url"],
        "document_title": record["title"],
        "speaker_or_author": None,
        "section": (
            " | ".join(
                value
                for value in [
                    record.get("grade"),
                    record.get("attribution"),
                    record.get("hadith_source"),
                ]
                if value
            )
            or None
        ),
        "text": combined_text,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        INPUT_DIR.glob("*.json")
    )

    if not files:
        raise RuntimeError(
            "No HadeethEnc records found"
        )

    created = 0

    for path in files:
        record = load_record(path)

        document = build_source_document(
            record
        )

        hadith_id = record["hadith_id"]

        output_file = (
            OUTPUT_DIR
            / f"hadeethenc_{hadith_id}.json"
        )

        with output_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                document,
                file,
                ensure_ascii=False,
                indent=2,
            )

        created += 1

        print(
            f"[OK] {hadith_id}: "
            f"{document['document_title']}"
        )

    print()
    print("Created:", created)
    print("Output:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
