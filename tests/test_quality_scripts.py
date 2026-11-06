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


class ExtractedBrandManifestChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "branding" / "v1.4"
        self.root.mkdir(parents=True)
        self.verifier = load_script("verify_branding")
        self.data = b"verified-brand"
        self.asset = self.root / "logos" / "mark.svg"
        self.asset.parent.mkdir()
        self.asset.write_bytes(self.data)
        self.manifest = {
            "file_count": 1,
            "files": {
                "logos/mark.svg": {
                    "size_bytes": len(self.data),
                    "sha256": hashlib.sha256(self.data).hexdigest(),
                }
            },
        }
        (self.root / "MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_exact_manifest_passes_strict_mode(self):
        self.assertEqual(self.verifier.verify(self.root, strict=True), 0)

    def test_extra_file_rejected_in_strict_mode(self):
        (self.root / "unexpected.txt").write_text("placeholder", encoding="utf-8")
        self.assertEqual(self.verifier.verify(self.root, strict=True), 1)

    def test_extra_file_remains_compatible_in_normal_mode(self):
        (self.root / "integration-notes.txt").write_text("note", encoding="utf-8")
        self.assertEqual(self.verifier.verify(self.root), 0)

    def test_modified_declared_file_is_rejected_in_strict_mode(self):
        self.asset.write_bytes(b"tampered")
        self.assertEqual(self.verifier.verify(self.root, strict=True), 1)


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


    def test_noncanonical_zip_path_rejected(self):
        archive = self.root / "noncanonical.zip"
        data = b"asset"
        manifest = {"file_count": 1, "files": {
            "logos//mark.svg": {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        }}
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            z.writestr("branding/v1.4/logos//mark.svg", data)
        self.assertEqual(self.checker.verify(archive), 1)

    def test_case_insensitive_collision_rejected(self):
        archive = self.root / "case-collision.zip"
        data = b"asset"
        manifest = {"file_count": 2, "files": {
            key: {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for key in ("logos/Mark.svg", "logos/mark.svg")
        }}
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            for key in manifest["files"]:
                z.writestr("branding/v1.4/" + key, data)
        self.assertEqual(self.checker.verify(archive), 1)



class BrandingInstallChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "branding").mkdir()
        (self.root / "branding" / "README.md").write_text("integration", encoding="utf-8")
        (self.root / "ROADMAP.md").write_text("roadmap", encoding="utf-8")
        self.installer = load_script("install_branding")

    def make_zip(self, *, mismatch=False):
        data = b"asset"
        manifest = {
            "file_count": 1,
            "files": {
                "logos/mark.svg": {
                    "size_bytes": len(data),
                    "sha256": "0" * 64 if mismatch else hashlib.sha256(data).hexdigest(),
                }
            },
        }
        archive = self.root / "brand.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            z.writestr("branding/v1.4/logos/mark.svg", data)
        return archive

    def test_install_valid_package(self):
        self.assertEqual(self.installer.install(self.make_zip(), self.root), 0)
        self.assertEqual((self.root / "branding/v1.4/logos/mark.svg").read_bytes(), b"asset")

    def test_reject_modified_package_without_writing(self):
        self.assertEqual(self.installer.install(self.make_zip(mismatch=True), self.root), 1)
        self.assertFalse((self.root / "branding/v1.4").exists())

    def test_refuse_overwrite(self):
        archive = self.make_zip()
        (self.root / "branding/v1.4").mkdir()
        self.assertEqual(self.installer.install(archive, self.root), 1)

    def test_reject_unrelated_directory(self):
        archive = self.make_zip()
        (self.root / "ROADMAP.md").unlink()
        self.assertEqual(self.installer.install(archive, self.root), 1)

    def test_noncanonical_manifest_path_rejected(self):
        data = b"asset"
        archive = self.root / "noncanonical.zip"
        manifest = {"file_count": 1, "files": {
            "logos//mark.svg": {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        }}
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            z.writestr("branding/v1.4/logos//mark.svg", data)
        self.assertEqual(self.installer.install(archive, self.root), 1)
        self.assertFalse((self.root / "branding/v1.4").exists())

    def test_case_collision_rejected_without_writing(self):
        data = b"asset"
        archive = self.root / "collision.zip"
        manifest = {"file_count": 2, "files": {
            key: {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for key in ("logos/Mark.svg", "logos/mark.svg")
        }}
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("branding/v1.4/MANIFEST.json", json.dumps(manifest))
            for key in manifest["files"]:
                z.writestr("branding/v1.4/" + key, data)
        self.assertEqual(self.installer.install(archive, self.root), 1)
        self.assertFalse((self.root / "branding/v1.4").exists())


if __name__ == "__main__":
    unittest.main()
