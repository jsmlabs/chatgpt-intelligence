"""Release candidate hardening: offline gate reports, fail-closed evidence and SemVer."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_release.py"
SPEC = importlib.util.spec_from_file_location("check_release_hardened", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class ReleaseHardeningTests(unittest.TestCase):
    def invoke(self, *args):
        stream = StringIO()
        with patch("sys.argv", ["check_release.py", *args]), redirect_stdout(stream):
            code = checker.main()
        return code, stream.getvalue()

    def test_json_report_is_single_object_and_blocks_unattested_release(self):
        failures = [gate + ": not passed" for gate in checker.REQUIRED_GATES]
        with patch.object(checker, "check", return_value=failures):
            code, output = self.invoke("--root", str(ROOT), "--json")
        self.assertEqual(code, 1)
        result = json.loads(output)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["release_approved"])
        self.assertFalse(result["publication_permitted"])
        self.assertTrue(result["human_review_required"])
        self.assertEqual(set(result["required_gates"]), set(checker.REQUIRED_GATES))
        self.assertGreaterEqual(result["failure_count"], len(checker.REQUIRED_GATES))
        for gate in checker.REQUIRED_GATES:
            self.assertTrue(any(gate in failure for failure in result["failures"]))

    def test_report_only_never_implies_approval(self):
        with patch.object(checker, "check", return_value=["fresh_chat_intel: not passed"]):
            code, output = self.invoke("--root", str(ROOT), "--report-only", "--json")
        self.assertEqual(code, 0)
        report = json.loads(output)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["publication_permitted"])

    def test_bad_evidence_references_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "quality").mkdir()
            (root / "quality" / "evidence.md").write_text("# Review")
            self.assertFalse(checker.evidence_reference_valid("../outside.md", root))
            self.assertFalse(checker.evidence_reference_valid("http://example.com", root))
            self.assertFalse(checker.evidence_reference_valid("https://person:password@example.com", root))
            self.assertFalse(checker.evidence_reference_valid("quality/missing.md", root))
            self.assertTrue(checker.evidence_reference_valid("quality/evidence.md", root))

    def test_cli_semver_is_a_valid_unpublished_candidate(self):
        # CLI SemVer is distinct from branding package v1.4 and historic
        # document metadata. No release tag or external package is implied.
        from intel import VERSION
        self.assertRegex(VERSION, r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
        self.assertTrue(VERSION)


if __name__ == "__main__":
    unittest.main()
