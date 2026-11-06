"""Regression tests for the per-case /INTEL record validator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_intel_e2e.py"
SPEC = importlib.util.spec_from_file_location("verify_intel_e2e", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class IntelE2ERecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "results.json"
        self.cases = [
            {
                "case_id": f"E2E-{index:02d}",
                "result": "passed",
                "tested_on": "2026-11-06",
                "surface": "manually reviewed fresh ChatGPT chat",
                "source_revision": "abc123",
                "evidence": f"test-evidence-{index:02d}.md",
            }
            for index in range(1, 13)
        ]

    def save(self):
        self.file.write_text(json.dumps({"cases": self.cases}), encoding="utf-8")

    def test_complete_records_are_structurally_valid(self):
        self.save()
        self.assertEqual(VALIDATOR.validate(self.file), [])

    def test_not_run_blocks_release(self):
        self.cases[0]["result"] = "not-run"
        self.save()
        self.assertTrue(any("E2E-01: not passed" in e for e in VALIDATOR.validate(self.file)))

    def test_missing_evidence_blocks_release(self):
        self.cases[0]["evidence"] = None
        self.save()
        self.assertTrue(any("E2E-01: passed but evidence is missing" in e for e in VALIDATOR.validate(self.file)))

    def test_duplicate_case_and_missing_case_rejected(self):
        self.cases[1]["case_id"] = "E2E-01"
        self.save()
        errors = VALIDATOR.validate(self.file)
        self.assertTrue(any("duplicate" in e for e in errors))
        self.assertTrue(any("E2E-02: missing case" in e for e in errors))

    def test_invalid_json_is_rejected(self):
        self.file.write_text("{bad json", encoding="utf-8")
        self.assertTrue(any("invalid E2E results file" in e for e in VALIDATOR.validate(self.file)))


if __name__ == "__main__":
    unittest.main()
