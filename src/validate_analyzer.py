"""Validate Analyzer v1 records for aggregation readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "analyzed" / "cgpsc_2025_analyzed.json"


def validate(document: dict) -> list[str]:
    errors = []
    questions = document.get("questions", [])
    record_ids = [question.get("record_id") for question in questions]
    if len(record_ids) != len(set(record_ids)):
        errors.append("record_id values are not unique")

    required_classification = {"subject_id", "topic_id", "subtopic_id"}
    for question in questions:
        number = question.get("question_no")
        if not question.get("record_id"):
            errors.append(f"question {number}: missing record_id")
        primary = question.get("classification", {}).get("primary", {})
        missing = required_classification - set(primary)
        if missing:
            errors.append(f"question {number}: missing classification fields {sorted(missing)}")
        aggregation = question.get("aggregation", {})
        for field in ("exam_year", "subject_id", "topic_id", "subtopic_id", "question_type", "difficulty"):
            if not aggregation.get(field):
                errors.append(f"question {number}: missing aggregation.{field}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    errors = validate(document)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"valid": True, "questions": len(document["questions"])}, indent=2))


if __name__ == "__main__":
    main()
