"""Regression tests for public brand media format verification."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_brand_media.py"
SPEC = importlib.util.spec_from_file_location("check_brand_media", SCRIPT)
assert SPEC and SPEC.loader
MEDIA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MEDIA)


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xffffffff
    )


def png(width: int = 16, height: int = 16) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    data = zlib.compress(b"".join(b"\x00" + b"\x00" * (width * 4) for _ in range(height)))
    return MEDIA.PNG_HEADER + chunk(b"IHDR", ihdr) + chunk(b"IDAT", data) + chunk(b"IEND", b"")


class BrandMediaChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "icons").mkdir()
        self.assets: dict[str, bytes] = {
            "icons/icon.png": png(),
            "icons/icon.svg": (
                b'<svg xmlns="http://www.w3.org/2000/svg" '
                b'width="16" height="16" viewBox="0 0 16 16"></svg>'
            ),
            "showcase.html": b'<html><img src="icons/icon.png"></html>',
        }
        self.save()

    def save(self):
        for name, data in self.assets.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (self.root / "MANIFEST.json").write_text(
            json.dumps({"files": {name: {} for name in self.assets}}),
            encoding="utf-8",
        )

    def test_valid_media(self):
        self.assertEqual(MEDIA.verify(self.root), ({"png": 1, "svg": 1, "html": 1}, []))

    def test_png_crc_rejection(self):
        damaged = bytearray(png())
        damaged[20] ^= 1
        with self.assertRaises(ValueError):
            MEDIA.png_dimensions(bytes(damaged))

    def test_png_truncated_rejection(self):
        with self.assertRaises(ValueError):
            MEDIA.png_dimensions(png()[:-4])

    def test_svg_not_well_formed(self):
        self.assets["icons/icon.svg"] = b"<svg"
        self.save()
        self.assertTrue(MEDIA.verify(self.root)[1])

    def test_svg_script_rejected(self):
        self.assets["icons/icon.svg"] = (
            b'<svg xmlns="http://www.w3.org/2000/svg" '
            b'width="16" height="16"><script /></svg>'
        )
        self.save()
        self.assertTrue(any("script" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_svg_event_handler_rejected(self):
        self.assets["icons/icon.svg"] = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
            b'onload="alert(1)"></svg>'
        )
        self.save()
        self.assertTrue(any("event-handler" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_svg_external_resource_rejected(self):
        self.assets["icons/icon.svg"] = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
            b'<image href="https://example.test/payload.png"/></svg>'
        )
        self.save()
        self.assertTrue(any("external SVG" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_html_remote_resource_rejected(self):
        self.assets["showcase.html"] = b'<img src="https://example.test/external.png">'
        self.save()
        self.assertTrue(any("external or executable HTML" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_html_script_protocol_rejected(self):
        self.assets["showcase.html"] = b'<img src="javascript:alert(1)">'
        self.save()
        self.assertTrue(any("external or executable HTML" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_png_svg_dimension_mismatch(self):
        self.assets["icons/icon.png"] = png(width=32)
        self.save()
        self.assertTrue(any("dimensions disagree" in issue for issue in MEDIA.verify(self.root)[1]))

    def test_missing_html_reference(self):
        self.assets["showcase.html"] = b'<img src="missing.png">'
        self.save()
        self.assertTrue(any("broken local HTML asset" in issue for issue in MEDIA.verify(self.root)[1]))


if __name__ == "__main__":
    unittest.main()
