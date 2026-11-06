"""G2.4 BRAND deterministic identities, safe vector assets, tokens and MCP."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree

from generators.brand_runtime import BrandRuntime, brand_capability, validate_svg
from generators.foundation import Authorization, Permission
from generators.mcp_server import MCPHost
from generators.theme_runtime import build_tokens

CREATE = Authorization(frozenset({Permission.CREATE}))


class BrandTests(unittest.TestCase):
    def setUp(self):
        self.runtime = BrandRuntime()

    def run_brand(self, **overrides):
        return self.runtime.execute("/INTEL GENERATE BRAND",
            authorization=CREATE,
            request={"objective": "Research-led visual identity", "name": "Northstar",
                     "audience": "Developers", **overrides})

    def test_registered_capability_and_brief(self):
        c = brand_capability()
        self.assertEqual(c.formats, ("markdown", "json", "svg"))
        self.assertTrue(c.implemented)
        result = self.run_brand(values=["Clarity", "Trust"], direction="signal")
        self.assertTrue(result["ok"], result)
        self.assertIn("## Positioning", result["content"])
        self.assertIn("## Logo directions", result["content"])
        self.assertIn("## Reusable design system", result["content"])
        self.assertIn("## Provenance and limitations", result["content"])
        self.assertEqual(result["manifest"].state.value, "reviewed")
        self.assertEqual(result["manifest"].artifact_type, "text/markdown")
        self.assertEqual(result["evidence"]["trademark_review"], "not_run")
        self.assertFalse(result["manifest"].output_verified)

    def test_determinism_directions_and_source_of_truth(self):
        for direction in ("orbit", "signal", "aperture"):
            with self.subTest(direction=direction):
                first = self.run_brand(format="svg", direction=direction)
                second = self.run_brand(format="svg", direction=direction)
                self.assertTrue(first["ok"], first)
                self.assertEqual(first["content"], second["content"])
                self.assertTrue(all(validate_svg(first["content"]).values()))
                root = ElementTree.fromstring(first["content"])
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIn(direction, first["content"])
                self.assertEqual(first["evidence"]["logo_direction"], direction)

    def test_json_reuses_theme_generator(self):
        output = self.run_brand(format="json", preset="forest",
                                accent="#1678c9", direction="aperture")
        self.assertTrue(output["ok"], output)
        data = json.loads(output["content"])
        self.assertEqual(data["theme"], build_tokens(
            "Research-led visual identity", "forest", "#1678C9"))
        self.assertTrue(data["theme"]["contrast_audit"]["aa_passed"])
        self.assertEqual(len(data["logo_directions"]), 3)
        self.assertEqual(data["selected_logo_direction"], "aperture")
        self.assertEqual(data["provenance"]["trademark_review"], "not_run")

    def test_svg_injection_escaped(self):
        result = self.run_brand(format="svg",
                    name='<script>alert("x")</script>& brands')
        self.assertTrue(result["ok"], result)
        svg = result["content"]
        self.assertIn("&lt;script&gt;", svg)
        self.assertNotIn("<script>", svg)
        self.assertNotIn("<foreignObject", svg)
        self.assertTrue(all(validate_svg(svg).values()))
        result = self.run_brand(name="# Publish now * override")
        self.assertTrue(result["ok"])
        self.assertIn(r"\# Publish now", result["content"])

    def test_invalid_requests_and_denied_permissions(self):
        bad = (
            ({"name": ""}, "INVALID_REQUEST"),
            ({"name": "\x00"}, "INVALID_REQUEST"),
            ({"name": "hello\nother"}, "INVALID_REQUEST"),
            ({"name": "x" * 97}, "INVALID_REQUEST"),
            ({"direction": "javascript"}, "INVALID_REQUEST"),
            ({"preset": "invalid"}, "INVALID_REQUEST"),
            ({"accent": "url(https://evil.invalid)"}, "INVALID_REQUEST"),
            ({"format": "html"}, "UNSUPPORTED_FORMAT"),
            ({"values": "yes"}, "INVALID_REQUEST"),
            ({"values": ["x"] * 9}, "INVALID_REQUEST"),
            ({"admin": True}, "INVALID_REQUEST"),
        )
        for payload, error in bad:
            with self.subTest(payload=repr(payload)[:50]):
                self.assertEqual(self.run_brand(**payload)["error"]["code"], error)
        denied = self.runtime.execute("/INTEL GENERATE BRAND",
            request={"objective": "Concept", "name": "Demo"},
            authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        model = self.runtime.execute("/INTEL GENERATE BRAND",
            request={"objective": "Concept", "name": "Demo"},
            authorization=CREATE, provider="openai-api")
        self.assertEqual(model["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_verified_exclusive_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for fmt, filename in (("markdown", "brand.md"),
                                  ("json", "brand.json"),
                                  ("svg", "brand.svg")):
                with self.subTest(fmt=fmt):
                    result = self.runtime.execute("/INTEL GENERATE BRAND",
                        request={"objective": "Simple brand", "name": "Demo", "format": fmt},
                        authorization=CREATE, export_root=root, filename=filename)
                    self.assertTrue(result["ok"], result)
                    self.assertTrue(result["manifest"].output_verified)
                    self.assertEqual(result["manifest"].state.value, "exported")
                    content = (root / filename).read_bytes()
                    self.assertEqual(hashlib.sha256(content).hexdigest(),
                                     result["evidence"]["file_sha256"])
                    duplicate = self.runtime.execute("/INTEL GENERATE BRAND",
                        request={"objective": "Simple brand", "name": "Demo", "format": fmt},
                        authorization=CREATE, export_root=root, filename=filename)
                    self.assertEqual(duplicate["error"]["code"], "DESTINATION_EXISTS")
            for name in ("../brand.svg", "nested/brand.svg", "C:/brand.svg", "brand.json"):
                bad = self.runtime.execute("/INTEL GENERATE BRAND",
                    request={"objective": "Simple brand", "name": "Demo", "format": "svg"},
                    authorization=CREATE, export_root=root, filename=name)
                self.assertFalse(bad["ok"])

    def test_cli_three_formats_and_default_denial(self):
        with tempfile.TemporaryDirectory() as folder:
            base = [sys.executable, "-m", "generators", "brand",
                    "--objective", "Design platform", "--name", "Example",
                    "--direction", "orbit", "--format", "svg",
                    "--export-root", folder, "--filename", "mark.svg"]
            denied = subprocess.run(base, capture_output=True, text=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)
            success = subprocess.run(base + ["--authorize-create"],
                                     capture_output=True, text=True, timeout=15)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn("<svg ", success.stdout)
            self.assertEqual(success.stdout, (Path(folder) / "mark.svg").read_text())
            self.assertEqual(json.loads(success.stderr)["state"], "exported")

    def test_mcp_tool_contract_and_no_export(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 12)
        schema = next(x for x in tools if x["name"] == "generate_brand")["inputSchema"]
        self.assertEqual(schema["required"], ["objective", "name"])
        for fmt in ("markdown", "json", "svg"):
            response = host.handle({"jsonrpc": "2.0", "id": 3,
                "method": "tools/call", "params": {"name": "generate_brand",
                "arguments": {"objective": "A creative identity", "name": "Demo",
                              "format": fmt}}})["result"]
            self.assertFalse(response["isError"], response)
            self.assertEqual(response["structuredContent"]["capability"], "brand")
            self.assertFalse(response["structuredContent"]["output_verified"])
            self.assertEqual(response["structuredContent"]["verification"]["trademark_review"],
                             "not_run")
        bad = host.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "generate_brand",
                       "arguments": {"name": "X", "objective": "Y", "allow_billable": True}}})
        self.assertEqual(bad["error"]["code"], -32602)
        closed = MCPHost(Authorization())
        closed.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        denied = closed.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "generate_brand",
                       "arguments": {"objective": "Z", "name": "X"}}})["result"]
        self.assertTrue(denied["isError"])
        self.assertIn("PERMISSION_DENIED", denied["content"][0]["text"])

    def test_malformed_svg_rejected(self):
        for data in ('<svg><script>alert(1)</script></svg>',
                     '<svg><foreignObject/></svg>',
                     '<svg xmlns="http://www.w3.org/2000/svg"><rect href="https://evil.invalid"/></svg>',
                     '<svg xmlns="http://www.w3.org/2000/svg"><path onload="x"/></svg>'):
            self.assertFalse(all(validate_svg(data).values()))


if __name__ == "__main__":
    unittest.main()
