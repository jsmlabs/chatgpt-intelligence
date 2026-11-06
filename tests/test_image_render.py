"""G2.1.1 actual local procedural PNG rendering tests; no external model."""
from __future__ import annotations
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from generators.foundation import Authorization, IntelError, Permission
from generators.image_render import render_image, validate_png, export_png, render_abstract_png
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class LocalImageRendererTests(unittest.TestCase):
    def test_valid_real_png_and_repeatability(self):
        a = render_image("geometric cover", aspect_ratio="16:9", authorization=CREATE)
        b = render_image("geometric cover", aspect_ratio="16:9", authorization=CREATE)
        self.assertTrue(a.png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(a.png, b.png)
        self.assertEqual(a.sha256, b.sha256)
        self.assertEqual((a.width, a.height), validate_png(a.png))
        self.assertGreater(a.width, a.height)
        self.assertLess(len(a.png), 512 * 1024)
        self.assertEqual(a.model_provider, "not-used")

    def test_different_seed_and_palette(self):
        a = render_abstract_png("one")
        b = render_abstract_png("two")
        c = render_abstract_png("one", palette="#000000,#ff0000,#ffffff")
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)

    def test_aspect_ratios(self):
        for ratio in ("1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16"):
            with self.subTest(ratio=ratio):
                image = render_image("sample", aspect_ratio=ratio, authorization=CREATE)
                self.assertEqual(validate_png(image.png), (image.width, image.height))

    def test_invalid_inputs_and_permission(self):
        with self.assertRaises(IntelError) as denied:
            render_image("test")
        self.assertEqual(denied.exception.code, "PERMISSION_DENIED")
        for kwargs in ({"aspect_ratio": "99:1"}, {"palette": "#123456,#abcdef"},
                       {"palette": "#zzzzzz,#111111,#ffffff"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(IntelError):
                render_image("test", authorization=CREATE, **kwargs)

    def test_corrupt_png_rejected(self):
        original = render_abstract_png("test")
        for data in (original[:-1], original + b"junk",
                     original[:50] + bytes([original[50] ^ 1]) + original[51:]):
            with self.subTest(length=len(data)), self.assertRaises(IntelError):
                validate_png(data)

    def test_exclusive_export_and_verified_readback(self):
        with tempfile.TemporaryDirectory() as d:
            image = render_image("export", authorization=CREATE)
            path, digest = export_png(image, Path(d), "poster.png")
            self.assertEqual(path, "poster.png")
            self.assertEqual(digest, image.sha256)
            self.assertEqual((Path(d) / path).read_bytes(), image.png)
            with self.assertRaises(IntelError) as existing:
                export_png(image, Path(d), path)
            self.assertEqual(existing.exception.code, "DESTINATION_EXISTS")
            for name in ("../escape.png", "/tmp/x.png", "a/b.png", "foo.md"):
                with self.assertRaises(IntelError):
                    export_png(image, Path(d), name)

    def test_cli_no_permission_and_success(self):
        with tempfile.TemporaryDirectory() as d:
            args = [sys.executable, "-m", "generators.image_render", "--objective",
                    "Poster", "--export-root", d, "--filename", "poster.png"]
            denied = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)
            accepted = subprocess.run(args + ["--authorize-create"], capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            output = json.loads(accepted.stdout)
            self.assertEqual(output["artifact_type"], "image/png")
            self.assertTrue(output["image_verified"])
            self.assertFalse(output["semantic_prompt_followed"])
            self.assertTrue((Path(d) / "poster.png").exists())

    def test_mcp_returns_actual_png_content(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 15)
        response = host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                "params": {"name": "render_abstract_image",
                                           "arguments": {"objective": "cover", "aspect_ratio": "9:16"}}})["result"]
        self.assertFalse(response["isError"], response)
        image = response["content"][0]
        self.assertEqual(image["type"], "image")
        self.assertEqual(image["mimeType"], "image/png")
        raw = base64.b64decode(image["data"], validate=True)
        self.assertEqual(validate_png(raw), (response["structuredContent"]["width"],
                                              response["structuredContent"]["height"]))
        self.assertTrue(response["structuredContent"]["image_verified"])
        self.assertEqual(response["structuredContent"]["model_provider"], "not-used")

    def test_mcp_denies_without_create(self):
        host = MCPHost()
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        response = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                "params": {"name": "render_abstract_image",
                                           "arguments": {"objective": "cover"}}})["result"]
        self.assertTrue(response["isError"])
        self.assertIn("PERMISSION_DENIED", response["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
