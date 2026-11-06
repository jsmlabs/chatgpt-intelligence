"""Tests for the fail-closed release readiness checker."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "check_release.py"
SPEC = importlib.util.spec_from_file_location("check_release", SOURCE)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text(CHECKER.TAGLINE, encoding="utf-8")
        for domain in CHECKER.DOMAINS:
            path = self.root / domain / "README.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Index\n", encoding="utf-8")
        (self.root / "quality").mkdir()
        self.evidence = {
            key: {"status": "not-run", "evidence": None}
            for key in CHECKER.REQUIRED_GATES
        }
        self.save()

    def save(self):
        (self.root / "quality/release-evidence.json").write_text(
            json.dumps(self.evidence), encoding="utf-8"
        )

    def test_missing_brand_blocks(self):
        errors = CHECKER.check(self.root)
        self.assertTrue(any("MANIFEST.json" in e for e in errors))

    def test_missing_client_evidence_blocks(self):
        errors = CHECKER.check(self.root)
        self.assertTrue(any("fresh_chat_intel: not passed" in e for e in errors))

    def test_passed_without_reference_blocks(self):
        self.evidence["fresh_chat_intel"] = {"status": "passed", "evidence": ""}
        self.save()
        errors = CHECKER.check(self.root)
        self.assertTrue(any("missing supporting evidence" in e for e in errors))

    def test_missing_domain_index_blocks(self):
        (self.root / "memory/README.md").unlink()
        errors = CHECKER.check(self.root)
        self.assertTrue(any("memory/README.md" in e for e in errors))

    def test_invalid_evidence_blocks(self):
        (self.root / "quality/release-evidence.json").write_text("{invalid", encoding="utf-8")
        errors = CHECKER.check(self.root)
        self.assertTrue(any("release-evidence.json" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
