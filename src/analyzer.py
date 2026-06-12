"""Taxonomy-driven CGPSC Analyzer v1.

Enriches Reader question JSON with a stable classification path, alternatives,
difficulty, and aggregation keys suitable for multi-year analysis.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "json" / "questions_draft.json"
DEFAULT_TAXONOMY = PROJECT_ROOT / "data" / "taxonomy" / "cgpsc_taxonomy_v1.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "analyzed" / "cgpsc_2025_analyzed.json"


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9%.\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def option_text(question: dict) -> str:
    return normalize(" ".join(str(value) for value in question.get("options", {}).values()))


def keyword_score(text: str, keywords: list) -> tuple[float, list[str]]:
    score = 0.0
    evidence = []
    for item in keywords:
        if isinstance(item, str):
            term, weight = item, 1.0
        else:
            term, weight = item["term"], float(item.get("weight", 1.0))
        normalized_term = normalize(term)
        if normalized_term and re.search(rf"\b{re.escape(normalized_term)}\b", text):
            score += weight
            evidence.append(term)
    return score, evidence


def flatten_taxonomy(taxonomy: dict) -> list[dict]:
    def scaled(keywords: list, multiplier: float, level: str) -> list[dict]:
        result = []
        for item in keywords:
            if isinstance(item, str):
                result.append({"term": item, "weight": multiplier, "level": level})
            else:
                result.append(
                    {
                        "term": item["term"],
                        "weight": float(item.get("weight", 1.0)) * multiplier,
                        "level": level,
                    }
                )
        return result

    leaves = []
    for subject in taxonomy["subjects"]:
        for topic in subject["topics"]:
            for subtopic in topic["subtopics"]:
                leaves.append(
                    {
                        "subject_id": subject["id"],
                        "subject": subject["label"],
                        "topic_id": topic["id"],
                        "topic": topic["label"],
                        "subtopic_id": subtopic["id"],
                        "subtopic": subtopic["label"],
                        "keywords": (
                            scaled(subject.get("keywords", []), 0.35, "subject")
                            + scaled(topic.get("keywords", []), 0.7, "topic")
                            + scaled(subtopic.get("keywords", []), 1.0, "subtopic")
                        ),
                    }
                )
    return leaves


def confidence_from_scores(best: float, second: float) -> float:
    if best <= 0:
        return 0.0
    margin = best - second
    return round(min(0.99, 0.45 + 0.08 * best + 0.06 * margin), 2)


def classify_taxonomy(text: str, leaves: list[dict], secondary_text: str = "") -> dict:
    ranked = []
    for leaf in leaves:
        score, evidence = keyword_score(text, leaf["keywords"])
        secondary_score, secondary_evidence = keyword_score(secondary_text, leaf["keywords"])
        score += secondary_score * 0.3
        evidence += [f"option:{term}" for term in secondary_evidence]
        if score:
            ranked.append({**leaf, "score": round(score, 2), "evidence": evidence})
    ranked.sort(key=lambda item: (-item["score"], item["subject_id"], item["topic_id"], item["subtopic_id"]))

    if not ranked:
        return {
            "primary": {
                "subject_id": "unclassified",
                "subject": "Unclassified",
                "topic_id": "unclassified",
                "topic": "Unclassified",
                "subtopic_id": "unclassified",
                "subtopic": "Unclassified",
            },
            "confidence": 0.0,
            "evidence": [],
            "alternatives": [],
            "needs_review": True,
        }

    best = ranked[0]
    second_score = ranked[1]["score"] if len(ranked) > 1 else 0.0
    primary = {key: best[key] for key in ("subject_id", "subject", "topic_id", "topic", "subtopic_id", "subtopic")}
    alternatives = [
        {
            **{key: item[key] for key in ("subject_id", "subject", "topic_id", "topic", "subtopic_id", "subtopic")},
            "score": item["score"],
        }
        for item in ranked[1:4]
    ]
    confidence = confidence_from_scores(best["score"], second_score)
    return {
        "primary": primary,
        "confidence": confidence,
        "evidence": best["evidence"],
        "alternatives": alternatives,
        "needs_review": confidence < 0.65,
    }


def classify_difficulty(question: dict, config: dict) -> dict:
    text = normalize(question.get("question", ""))
    score = float(config["base_score"])
    evidence = []

    question_type = question.get("type", "standard_mcq")
    type_weight = float(config["question_type_weights"].get(question_type, 0))
    if type_weight:
        score += type_weight
        evidence.append(f"type:{question_type}")

    for signal in config["signals"]:
        matches = sum(bool(re.search(rf"\b{re.escape(normalize(term))}\b", text)) for term in signal["keywords"])
        if matches:
            score += float(signal["weight"]) * matches
            evidence.append(signal["id"])

    option_count = len(question.get("options", {}))
    if option_count < 4:
        evidence.append("reader_output_incomplete")

    score = round(max(0.0, min(10.0, score)), 2)
    thresholds = config["thresholds"]
    if score < thresholds["medium"]:
        label = "easy"
    elif score < thresholds["hard"]:
        label = "medium"
    else:
        label = "hard"

    return {
        "label": label,
        "score": score,
        "confidence": 0.75 if option_count == 4 else 0.6,
        "evidence": evidence,
        "note": "Estimated from question form and knowledge demands; not answer-performance data.",
    }


def enrich_question(question: dict, taxonomy: dict, leaves: list[dict], exam: str, year: int) -> dict:
    classification = classify_taxonomy(normalize(question.get("question", "")), leaves, option_text(question))
    primary = classification["primary"]
    result = dict(question)
    result["record_id"] = f"cgpsc-prelims-{year}-q{question['question_no']:03d}"
    result["exam"] = exam
    result["year"] = year
    result["taxonomy_version"] = taxonomy["version"]
    result["classification"] = classification
    result["difficulty"] = classify_difficulty(question, taxonomy["difficulty"])
    result["aggregation"] = {
        "exam_year": f"cgpsc-prelims:{year}",
        "subject_id": primary["subject_id"],
        "topic_id": primary["topic_id"],
        "subtopic_id": primary["subtopic_id"],
        "question_type": question.get("type", "unknown"),
        "difficulty": result["difficulty"]["label"],
    }
    return result


def build_summary(questions: list[dict]) -> dict:
    def counts(path):
        return dict(sorted(Counter(path(question) for question in questions).items()))

    return {
        "questions": len(questions),
        "subjects": counts(lambda q: q["aggregation"]["subject_id"]),
        "topics": counts(lambda q: q["aggregation"]["topic_id"]),
        "difficulty": counts(lambda q: q["difficulty"]["label"]),
        "classification_review_count": sum(q["classification"]["needs_review"] for q in questions),
        "classification_review_question_numbers": [
            q["question_no"] for q in questions if q["classification"]["needs_review"]
        ],
    }


def analyze(document: dict, taxonomy: dict) -> dict:
    leaves = flatten_taxonomy(taxonomy)
    questions = [
        enrich_question(question, taxonomy, leaves, document.get("exam", "CGPSC Prelims"), document["year"])
        for question in document["questions"]
    ]
    return {
        "schema_version": "analyzer-record-v1",
        "taxonomy_version": taxonomy["version"],
        "exam": document.get("exam", "CGPSC Prelims"),
        "year": document["year"],
        "source_file": document.get("source_file"),
        "summary": build_summary(questions),
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("-t", "--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    document = json.loads(args.input.read_text(encoding="utf-8"))
    taxonomy = json.loads(args.taxonomy.read_text(encoding="utf-8"))
    result = analyze(document, taxonomy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
