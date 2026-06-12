"""Small regression tests for Analyzer v1."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from analyzer import analyze, flatten_taxonomy
from validate_analyzer import validate


READER_JSON = PROJECT_ROOT / "data" / "json" / "questions_draft.json"
TAXONOMY_JSON = PROJECT_ROOT / "data" / "taxonomy" / "cgpsc_taxonomy_v1.json"


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = json.loads(READER_JSON.read_text(encoding="utf-8"))
        cls.taxonomy = json.loads(TAXONOMY_JSON.read_text(encoding="utf-8"))
        cls.result = analyze(cls.reader, cls.taxonomy)

    def test_taxonomy_leaf_ids_are_unique(self):
        leaves = flatten_taxonomy(self.taxonomy)
        ids = [leaf["subtopic_id"] for leaf in leaves]
        self.assertEqual(len(ids), len(set(ids)))

    def test_output_is_aggregation_ready(self):
        self.assertEqual(validate(self.result), [])
        self.assertEqual(len(self.result["questions"]), 100)

    def test_known_anchor_classifications(self):
        expected = {
            9: "polity_governance.constitution.rights",
            21: "economy.money_banking.currency",
            31: "geography.human.cartography",
            43: "environment.ecology.ecosystems",
            97: "chhattisgarh_studies.society_culture.tribes",
        }
        for number, subtopic_id in expected.items():
            question = self.result["questions"][number - 1]
            self.assertEqual(question["classification"]["primary"]["subtopic_id"], subtopic_id)


if __name__ == "__main__":
    unittest.main()
