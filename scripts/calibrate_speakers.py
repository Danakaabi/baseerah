from pathlib import Path

from app.audio.speaker_identification import identify_speaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_DIR = PROJECT_ROOT / "data" / "speaker_calibration"

SPEAKERS = {
    "binbaz": "عبدالعزيز بن عبدالله بن باز",
    "binothaimeen": "محمد بن صالح العثيمين",
}


def main():
    total = 0
    correct = 0
    rows = []

    for expected_id, expected_name in SPEAKERS.items():
        speaker_dir = CALIBRATION_DIR / expected_id

        for audio_path in sorted(speaker_dir.glob("*.wav")):
            result = identify_speaker(audio_path)

            matches = result["all_matches"]
            best = matches[0]
            second = matches[1] if len(matches) > 1 else None

            best_score = best["speaker_similarity"]
            second_score = (
                second["speaker_similarity"]
                if second is not None
                else 0.0
            )

            margin = best_score - second_score
            is_correct = best["speaker_id"] == expected_id

            total += 1
            correct += int(is_correct)

            rows.append(
                {
                    "file": audio_path.name,
                    "expected": expected_name,
                    "predicted": best["speaker_name"],
                    "best_score": best_score,
                    "second_score": second_score,
                    "margin": margin,
                    "correct": is_correct,
                }
            )

    print("\n=== BASEERAH SPEAKER CALIBRATION ===\n")

    for row in rows:
        print(f"File:       {row['file']}")
        print(f"Expected:   {row['expected']}")
        print(f"Predicted:  {row['predicted']}")
        print(f"Best:       {row['best_score']:.4f}")
        print(f"Second:     {row['second_score']:.4f}")
        print(f"Margin:     {row['margin']:.4f}")
        print(f"Correct:    {'YES' if row['correct'] else 'NO'}")
        print("-" * 50)

    accuracy = correct / total if total else 0.0

    print("\n=== SUMMARY ===")
    print(f"Samples:  {total}")
    print(f"Correct:  {correct}")
    print(f"Accuracy: {accuracy:.2%}")


if __name__ == "__main__":
    main()
