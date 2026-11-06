"""Focused regression tests for the public tracked-text credential scan."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_publication_safety.py"
SPEC = importlib.util.spec_from_file_location("check_publication_safety", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class PublicationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name: str, text: str) -> Path:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_safe_markdown_has_no_findings(self):
        path = self.file("README.md", "No credentials here.")
        self.assertEqual(SCANNER.scan([path], self.root), (1, []))

    def test_github_token_signature_detected_without_disclosure(self):
        path = self.file("exposure.md", "ghp_" + "A" * 36)
        _, issues = SCANNER.scan([path], self.root)
        self.assertTrue(any("github-classic-token" in issue for issue in issues))
        self.assertTrue(all("A" * 36 not in issue for issue in issues))

    def test_private_key_header_is_detected(self):
        path = self.file("config.txt", "-----BEGIN " + "PRIVATE KEY-----")
        _, issues = SCANNER.scan([path], self.root)
        self.assertTrue(any("private-key-header" in issue for issue in issues))

    def test_untracked_binary_extension_not_scanned(self):
        path = self.root / "image.png"
        path.write_bytes(b"ghp_" + b"A" * 36)
        self.assertEqual(SCANNER.scan([path], self.root), (0, []))

    def test_oversize_text_is_blocked(self):
        path = self.root / "large.md"
        path.write_bytes(b"x" * (SCANNER.MAX_BYTES + 1))
        count, issues = SCANNER.scan([path], self.root)
        self.assertEqual(count, 0)
        self.assertTrue(any("oversize" in issue for issue in issues))

    def test_missing_tracked_file_is_blocked(self):
        count, issues = SCANNER.scan([self.root / "missing.md"], self.root)
        self.assertEqual(count, 0)
        self.assertTrue(any("missing tracked" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
