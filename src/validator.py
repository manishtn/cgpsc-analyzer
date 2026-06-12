"""Validate a draft CGPSC question JSON and produce a focused review report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "json" / "questions_draft.json"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "json" / "review_report.json"
EXPECTED_QUESTION_COUNT = 100
EXPECTED_OPTION_LABELS = {"A", "B", "C", "D"}


def validate(document: dict) -> dict:
    questions = document.get("questions", [])
    numbers = [question.get("question_no") for question in questions]
    expected_numbers = set(range(1, EXPECTED_QUESTION_COUNT + 1))
    actual_numbers = {number for number in numbers if isinstance(number, int)}

    review_items = []
    for question in questions:
        issues = list(question.get("warnings", []))
        labels = set(question.get("options", {}))

        if not question.get("question", "").strip():
            issues.append("empty question text")
        if labels != EXPECTED_OPTION_LABELS:
            issues.append(f"option labels found: {', '.join(sorted(labels)) or 'none'}")
        if issues:
            review_items.append(
                {
                    "question_no": question.get("question_no"),
                    "confidence": question.get("confidence"),
                    "issues": list(dict.fromkeys(issues)),
                    "question": question.get("question", ""),
                    "raw_text": question.get("raw_text", ""),
                }
            )

    duplicate_numbers = sorted({number for number in numbers if numbers.count(number) > 1})
    return {
        "valid_question_sequence": numbers == list(range(1, EXPECTED_QUESTION_COUNT + 1)),
        "questions_found": len(questions),
        "missing_question_numbers": sorted(expected_numbers - actual_numbers),
        "duplicate_question_numbers": duplicate_numbers,
        "questions_needing_review": len(review_items),
        "review_question_numbers": [item["question_no"] for item in review_items],
        "review_items": review_items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    document = json.loads(args.input.read_text(encoding="utf-8"))
    report = validate(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {key: value for key, value in report.items() if key not in {"review_items"}}
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
