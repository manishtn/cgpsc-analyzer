"""Draft parser for the supplied CGPSC OCR question paper.

This intentionally favors traceability over aggressive OCR correction. Every
question keeps its original OCR block and receives warnings when extraction is
incomplete or relies on a fuzzy option label.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw_text" / "ocr_output.txt"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "json" / "questions_draft.json"

QUESTION_COUNT = 100

MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u20ac\u2122": "\u2019",
    "\u00e2\u20ac\u02dc": "\u2018",
    "\u00e2\u20ac\u0153": "\u201c",
    "\u00e2\u20ac\ufffd": "\u201d",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00c2\u00b0": "\u00b0",
    "\u00c2\u00a9": "\u00a9",
    "\u00c2\u00ab": "\u00ab",
    "\u00e2\u201a\u00ac": "\u20ac",
}

FOOTER_RE = re.compile(r"^[^A-Za-z0-9]{0,8}\$24\s*-\s*25\s*$")
ISOLATED_NOISE_RE = re.compile(r"^[\s|\\/<>{}\[\]~_=+\-â€œâ€]+$")
QUESTION_TYPE_PATTERNS = (
    ("match_following", re.compile(r"\bmatch\b|\bcolumn\s*[-\u2014]?\s*i\b", re.I)),
    ("assertion_reason", re.compile(r"\bassertion\s*\(A\)|\breason\s*\(R\)", re.I)),
    (
        "statement_based",
        re.compile(r"\bconsider the following statements\b|\bstatements?\s+(?:is/are|are)\b", re.I),
    ),
    ("ordering", re.compile(r"\barrange\b|\bchronological order\b", re.I)),
)

EXACT_OPTION_ANY_RE = re.compile(r"[\(\{]([A-D])[\)\}]\s*")
FUZZY_OPTION_STARTS = (
    ("A", re.compile(r"^[^A-Za-z0-9]{0,8}(?:fA\]|[4JLA]A\)|UAY|JAX|\(AK|BY Ay)\s*")),
    ("B", re.compile(r"^[^A-Za-z0-9]{0,8}(?:\(?B(?:y|j|r)[\)\}]|By (?=[A-Z]\.))\s*")),
    ("C", re.compile(r"^[^A-Za-z0-9]{0,8}(?:4\u20ac\)|\(?C[\)\}])\s*")),
    ("D", re.compile(r"^[^A-Za-z0-9]{0,8}(?:\(?D[\)\}]|WF|\(y|UBy|\\pr)\s*")),
)


def repair_mojibake(text: str) -> str:
    for broken, repaired in MOJIBAKE_REPLACEMENTS.items():
        text = text.replace(broken, repaired)
    return text


def clean_line(line: str) -> str:
    line = repair_mojibake(line).strip()
    line = re.sub(r"\s+", " ", line)
    return line


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if FOOTER_RE.match(line):
        return True
    if ISOLATED_NOISE_RE.match(line):
        return True
    if re.fullmatch(r"[^A-Za-z0-9]{0,5}\d{1,2}\s*[\]\|][^A-Za-z0-9]{0,3}", line):
        return True
    return False


def question_start_match(line: str, expected: int) -> re.Match[str] | None:
    # Main question starts may have scan marks before the number. Requiring the
    # expected next number prevents list items inside questions becoming starts.
    pattern = re.compile(
        rf"^[^A-Za-z0-9]{{0,20}}{expected}[\.,]\s+(?P<body>.+)$",
        re.IGNORECASE,
    )
    return pattern.match(line)


def segment_questions(raw_text: str) -> list[dict]:
    raw_lines = raw_text.splitlines()
    questions: list[dict] = []
    current_raw: list[str] = []
    current_clean: list[str] = []
    current_number = 1
    expected = 2

    # Question 1's number is absent in this OCR, so the document beginning is
    # treated as question 1 and subsequent boundaries are sequence-aware.
    for raw_line in raw_lines:
        cleaned = clean_line(raw_line)
        match = question_start_match(cleaned, expected) if expected <= QUESTION_COUNT else None
        if match:
            questions.append(
                {
                    "number": current_number,
                    "raw_lines": current_raw,
                    "clean_lines": current_clean,
                }
            )
            current_number = expected
            expected += 1
            current_raw = [raw_line]
            current_clean = [match.group("body")]
            continue

        current_raw.append(raw_line)
        if not is_noise_line(cleaned):
            current_clean.append(cleaned)

    questions.append(
        {
            "number": current_number,
            "raw_lines": current_raw,
            "clean_lines": current_clean,
        }
    )
    return questions


def fuzzy_option_start(line: str) -> tuple[str, re.Match[str]] | None:
    for label, pattern in FUZZY_OPTION_STARTS:
        match = pattern.match(line)
        if match:
            return label, match
    return None


def exact_option_start(line: str) -> re.Match[str] | None:
    for match in EXACT_OPTION_ANY_RE.finditer(line):
        prefix = line[: match.start()]
        if match.start() <= 16 and not re.search(r"[A-Za-z]{3}", prefix):
            return match
    return None


def split_option_line(line: str) -> tuple[list[tuple[str, str]], bool]:
    first = exact_option_start(line)
    fuzzy = False

    if first:
        starts = [match for match in EXACT_OPTION_ANY_RE.finditer(line) if match.start() >= first.start()]
    else:
        fuzzy_start = fuzzy_option_start(line)
        if not fuzzy_start:
            return [], False
        label, match = fuzzy_start
        starts = [(label, match)]
        fuzzy = True

    parts: list[tuple[str, str]] = []
    for index, start in enumerate(starts):
        if isinstance(start, tuple):
            label, match = start
        else:
            label, match = start.group(1), start
        end = starts[index + 1][1].start() if index + 1 < len(starts) and isinstance(starts[index + 1], tuple) else (
            starts[index + 1].start() if index + 1 < len(starts) else len(line)
        )
        parts.append((label.upper(), line[match.end() : end].strip()))
    return parts, fuzzy


def join_fragments(fragments: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(fragment for fragment in fragments if fragment)).strip()


def classify_question(text: str) -> str:
    for question_type, pattern in QUESTION_TYPE_PATTERNS:
        if pattern.search(text):
            return question_type
    return "standard_mcq"


def parse_question(block: dict) -> dict:
    question_fragments: list[str] = []
    option_fragments: dict[str, list[str]] = {}
    option_order: list[str] = []
    warnings: list[str] = []
    current_option: str | None = None
    fuzzy_labels: set[str] = set()

    for line in block["clean_lines"]:
        option_parts, fuzzy = split_option_line(line)
        if option_parts:
            for label, text in option_parts:
                if label in option_fragments:
                    warnings.append(f"duplicate option label {label}")
                else:
                    option_fragments[label] = []
                    option_order.append(label)
                if text:
                    option_fragments[label].append(text)
                current_option = label
                if fuzzy:
                    fuzzy_labels.add(label)
            continue

        if current_option:
            option_fragments[current_option].append(line)
        else:
            question_fragments.append(line)

    options = {label: join_fragments(option_fragments.get(label, [])) for label in "ABCD" if label in option_fragments}
    missing = [label for label in "ABCD" if label not in options]
    if missing:
        warnings.append(f"missing option labels: {', '.join(missing)}")
    if option_order != sorted(option_order, key="ABCD".index):
        warnings.append(f"unexpected option order: {', '.join(option_order)}")
    if fuzzy_labels:
        warnings.append(f"fuzzy option labels inferred: {', '.join(sorted(fuzzy_labels))}")
    if block["number"] == 1:
        warnings.append("question number 1 inferred from document start")

    question_text = join_fragments(question_fragments)
    confidence = 1.0
    confidence -= 0.12 * len(missing)
    confidence -= 0.05 * len(fuzzy_labels)
    confidence -= 0.05 if any("duplicate" in warning or "unexpected" in warning for warning in warnings) else 0
    confidence -= 0.05 if block["number"] == 1 else 0
    confidence = max(0.0, round(confidence, 2))

    return {
        "question_no": block["number"],
        "type": classify_question(question_text),
        "question": question_text,
        "options": options,
        "answer": None,
        "subject": None,
        "topic": None,
        "confidence": confidence,
        "warnings": warnings,
        "raw_text": "\n".join(block["raw_lines"]).strip(),
    }


def build_document(raw_text: str, source: Path) -> dict:
    blocks = segment_questions(raw_text)
    questions = [parse_question(block) for block in blocks]
    flagged = [question["question_no"] for question in questions if question["warnings"]]
    complete = [question["question_no"] for question in questions if len(question["options"]) == 4]
    option_count_distribution = {
        str(count): sum(len(question["options"]) == count for question in questions)
        for count in range(5)
    }
    return {
        "source_file": str(source),
        "exam": "CGPSC Prelims",
        "year": 2025,
        "draft": True,
        "summary": {
            "questions_extracted": len(questions),
            "expected_questions": QUESTION_COUNT,
            "questions_with_four_options": len(complete),
            "option_count_distribution": option_count_distribution,
            "questions_flagged_for_review": len(flagged),
            "flagged_question_numbers": flagged,
        },
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw_text = args.input.read_text(encoding="utf-8")
    document = build_document(raw_text, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(document["summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
