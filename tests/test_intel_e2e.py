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
        folder = Path(self.temp.name) / "quality"
        folder.mkdir()
        self.file = folder / "intel-e2e-results.json"
        self.cases = [
            {
                "case_id": f"E2E-{index:02d}",
                "result": "passed",
                "tested_on": "2026-11-06",
                "surface": "manually reviewed fresh ChatGPT chat",
                "source_revision": "a" * 40,
                "evidence": f"https://github.com/jsmlabs/chatgpt-intelligence/issues/{index}",
            }
            for index in range(1, 13)
        ]

    def save(self):
        self.file.write_text(json.dumps({"schema_version": 1, "cases": self.cases}), encoding="utf-8")

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
        self.assertTrue(any("E2E-01: evidence must be" in e for e in VALIDATOR.validate(self.file)))

    def test_duplicate_case_and_missing_case_rejected(self):
        self.cases[1]["case_id"] = "E2E-01"
        self.save()
        errors = VALIDATOR.validate(self.file)
        self.assertTrue(any("duplicate" in e for e in errors))
        self.assertTrue(any("E2E-02: missing case" in e for e in errors))

    def test_short_source_revision_is_rejected(self):
        self.cases[0]["source_revision"] = "abc123"
        self.save()
        self.assertTrue(any("full 40-character commit SHA" in e for e in VALIDATOR.validate(self.file)))

    def test_invalid_iso_date_is_rejected(self):
        self.cases[0]["tested_on"] = "2026-02-30"
        self.save()
        self.assertTrue(any("invalid or missing tested_on" in e for e in VALIDATOR.validate(self.file)))

    def test_relative_missing_evidence_is_rejected(self):
        self.cases[0]["evidence"] = "quality/missing-evidence.md"
        self.save()
        self.assertTrue(any("existing repository-relative file" in e for e in VALIDATOR.validate(self.file)))

    def test_http_evidence_is_rejected(self):
        self.cases[0]["evidence"] = "http://example.com/claim"
        self.save()
        self.assertTrue(any("HTTPS URL" in e for e in VALIDATOR.validate(self.file)))

    def test_local_evidence_is_accepted_when_present(self):
        folder = Path(self.temp.name) / "quality"
        (folder / "case01.md").write_text("sanitized observation", encoding="utf-8")
        self.cases[0]["evidence"] = "quality/case01.md"
        self.save()
        self.assertEqual(VALIDATOR.validate(self.file), [])

    def test_invalid_json_is_rejected(self):
        self.file.write_text("{bad json", encoding="utf-8")
        self.assertTrue(any("invalid E2E results file" in e for e in VALIDATOR.validate(self.file)))


if __name__ == "__main__":
    unittest.main()
