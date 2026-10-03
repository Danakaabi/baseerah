import argparse
import argparse
import json
import re
import time
import urllib.request
from html import unescape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "demo"
    / "hadeethenc"
)

BASE_URL = "https://hadeethenc.com/ar/browse/hadith"

DEFAULT_DEFAULT_HADITH_IDS = [
    "4560",
    "66540",
    "3591",
    "4555",
    "5331",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch trusted Arabic hadith records "
            "from HadeethEnc."
        )
    )

    parser.add_argument(
        "hadith_ids",
        nargs="*",
        help=(
            "HadeethEnc hadith IDs. "
            "If omitted, the demo IDs are used."
        ),
    )

    return parser.parse_args()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch trusted Arabic hadith records "
            "from HadeethEnc."
        )
    )

    parser.add_argument(
        "hadith_ids",
        nargs="*",
        help=(
            "HadeethEnc hadith IDs. "
            "If omitted, the demo IDs are used."
        ),
    )

    return parser.parse_args()


def fetch_page(hadith_id: str) -> str:
    url = f"{BASE_URL}/{hadith_id}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "BASEERAH-Hackathon/0.1"
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace",
        )


def extract_article(html: str) -> dict:
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>'
        r'(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    for raw_script in scripts:
        try:
            data = json.loads(
                unescape(raw_script.strip())
            )
        except json.JSONDecodeError:
            continue

        graph = data.get("@graph", [])

        if not isinstance(graph, list):
            continue

        for item in graph:
            if (
                isinstance(item, dict)
                and item.get("@type") == "Article"
                and item.get("genre") == "Hadith"
            ):
                return item

    raise ValueError(
        "Hadith Article JSON-LD was not found"
    )


def get_property(
    article: dict,
    name: str,
) -> str | None:
    properties = article.get(
        "additionalProperty",
        [],
    )

    target_name = name.casefold().replace(" ", "")

    for item in properties:
        if not isinstance(item, dict):
            continue

        property_name = str(
            item.get("name", "")
        ).casefold().replace(" ", "")

        if property_name == target_name:
            value = item.get("value")

            if isinstance(value, str):
                return value.strip()

    return None


def build_record(
    hadith_id: str,
    article: dict,
) -> dict:
    return {
        "hadith_id": hadith_id,
        "content_type": "hadith",
        "language": "ar",
        "title": article.get("headline"),
        "text": article.get("text"),
        "explanation": article.get("abstract"),
        "grade": get_property(
            article,
            "Hadithgrade",
        ),
        "attribution": get_property(
            article,
            "Attribution",
        ),
        "hadith_source": get_property(
            article,
            "Hadith source",
        ),
        "citation": article.get("citation"),
        "source_name": "HadeethEnc",
        "source_url": (
            f"{BASE_URL}/{hadith_id}"
        ),
    }


def save_record(record: dict) -> Path:
    output_file = (
        OUTPUT_DIR
        / f"{record['hadith_id']}.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            record,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_file


def main() -> None:
    args = parse_args()

    hadith_ids = (
        args.hadith_ids
        if args.hadith_ids
        else DEFAULT_HADITH_IDS
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    successful = 0
    failed = 0

    for position, hadith_id in enumerate(
        hadith_ids,
        start=1,
    ):
        print(
            f"[{position}/{len(hadith_ids)}] "
            f"Fetching {hadith_id}..."
        )

        try:
            html = fetch_page(hadith_id)

            article = extract_article(html)

            record = build_record(
                hadith_id,
                article,
            )

            if not record["text"]:
                raise ValueError(
                    "Hadith text is missing"
                )

            output_file = save_record(record)

            successful += 1

            print("  TITLE:", record["title"])
            print("  GRADE:", record["grade"])
            print("  SAVED:", output_file.name)

        except Exception as exc:
            failed += 1
            print(
                f"  ERROR: {type(exc).__name__}: "
                f"{exc}"
            )

        if position < len(hadith_ids):
            time.sleep(1)

        print()

    print("=" * 60)
    print("Successful:", successful)
    print("Failed:", failed)
    print("Directory:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
