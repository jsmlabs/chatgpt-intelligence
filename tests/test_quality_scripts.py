"""Regression tests for dependency-free repository verification tools."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DocumentationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checker = load_script("check_docs")

    def test_valid_relative_link(self):
        (self.root / "README.md").write_text("[Guide](guide.md)", encoding="utf-8")
        (self.root / "guide.md").write_text("# Guide", encoding="utf-8")
        self.assertEqual(self.checker.audit(self.root), (2, 1, []))

    def test_missing_link_fails(self):
        (self.root / "README.md").write_text("[Missing](missing.md)", encoding="utf-8")
        _, _, errors = self.checker.audit(self.root)
        self.assertTrue(any("missing" in item for item in errors))

    def test_invalid_frontmatter_fails(self):
        (self.root / "test.md").write_text(
            "---\nstatus: unsupported\nclassification: experimental\n---\n",
            encoding="utf-8",
        )
        _, _, errors = self.checker.audit(self.root)
        self.assertTrue(any("invalid status" in item for item in errors))

    def test_fenced_example_link_ignored(self):
        (self.root / "README.md").write_text(
            "```markdown\n[Example](not-real.md)\n```\n",
            encoding="utf-8",
        )
        self.assertEqual(self.checker.audit(self.root), (1, 0, []))


class BrandingArchiveChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checker = load_script("verify_branding_archive")

    def make_zip(self, *, mismatch=False, extra=None):
        data = b"test-brand-asset"
        digest = hashlib.sha256(data).hexdigest()
        if mismatch:
            digest = "0" * 64
        manifest = {
            "file_count": 1,
            "files": {"logos/mark.svg": {"size_bytes": len(data), "sha256": digest}},
        }
        target = self.root / "assets.zip"
        with zipfile.ZipFile(target, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            z.writestr("branding/v1.4/logos/mark.svg", data)
            if extra:
                z.writestr(extra, b"unexpected")
        return target

    def test_valid_archive(self):
        self.assertEqual(self.checker.verify(self.make_zip()), 0)

    def test_hash_mismatch(self):
        self.assertEqual(self.checker.verify(self.make_zip(mismatch=True)), 1)

    def test_extra_entry_rejected(self):
        self.assertEqual(self.checker.verify(self.make_zip(extra="branding/v1.4/extra.txt")), 1)

    def test_path_traversal_rejected(self):
        self.assertEqual(self.checker.verify(self.make_zip(extra="branding/v1.4/../escape")), 1)


if __name__ == "__main__":
    unittest.main()
