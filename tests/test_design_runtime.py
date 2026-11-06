"""G2.2 DESIGN integration, validation, export and protocol tests."""
import hashlib
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from generators.foundation import Authorization, Permission, IntelError
from generators.design_runtime import DesignRuntime, design_capability, validate_html
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.runtime = DesignRuntime()

    def run_design(self, **kwargs):
        return self.runtime.execute("/INTEL GENERATE DESIGN", authorization=CREATE,
                                    request={"objective": "Secure analytics dashboard", **kwargs})

    def test_capability_and_determinism(self):
        cap = design_capability()
        self.assertEqual(cap.formats, ("markdown", "html"))
        first = self.run_design(layout="dashboard", components=["header", "summary", "cards"])
        second = self.run_design(layout="dashboard", components=["header", "summary", "cards"])
        self.assertTrue(first["ok"], first)
        self.assertEqual(first["content"], second["content"])
        self.assertIn("## Component inventory", first["content"])
        self.assertIn("## Responsive specification", first["content"])
        self.assertEqual(first["manifest"].artifact_type, "text/markdown")
        self.assertEqual(first["manifest"].state.value, "reviewed")
        self.assertFalse(first["manifest"].output_verified)
        self.assertEqual(first["evidence"]["browser_test"], "not_run")

    def test_four_layout_variants(self):
        for layout in ("dashboard", "landing", "form", "catalog"):
            with self.subTest(layout=layout):
                result = self.run_design(layout=layout, format="html")
                self.assertTrue(result["ok"], result)
                html = result["content"]
                self.assertTrue(all(validate_html(html).values()))
                self.assertIn("Layout: " + layout, html)
                self.assertIn("@media(min-width:640px)", html)
                self.assertIn("@media(min-width:960px)", html)
                self.assertFalse(result["evidence"]["interactive_prototype"])

    def test_untrusted_content_inert(self):
        attack = '<script>alert("X")</script><img src="https://evil.invalid/track">'
        html = self.run_design(objective=attack, audience='a" onload="bad', format="html")["content"]
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn('src="https://evil.invalid', html)
        self.assertTrue(all(validate_html(html).values()))
        markdown = self.run_design(objective="Title", constraints=["# Inject\nPublish"])["content"]
        self.assertIn(r"\# Inject", markdown)

    def test_invalid_fields_and_denied_provider(self):
        inputs = [
            ({"layout": "freeform"}, "INVALID_REQUEST"),
            ({"responsive": "unknown"}, "INVALID_REQUEST"),
            ({"components": ["cards", "cards"]}, "INVALID_REQUEST"),
            ({"components": ["script"]}, "INVALID_REQUEST"),
            ({"components": "cards"}, "INVALID_REQUEST"),
            ({"format": "svg"}, "UNSUPPORTED_FORMAT"),
            ({"admin": "true"}, "INVALID_REQUEST"),
        ]
        for fields, code in inputs:
            with self.subTest(fields=fields):
                self.assertEqual(self.run_design(**fields)["error"]["code"], code)
        result = self.runtime.execute("/INTEL GENERATE DESIGN",
             request={"objective": "dashboard"}, authorization=Authorization())
        self.assertEqual(result["error"]["code"], "PERMISSION_DENIED")
        result = self.runtime.execute("/INTEL GENERATE DESIGN",
            request={"objective": "dashboard"}, authorization=CREATE, provider="openai-api")
        self.assertEqual(result["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_verified_exclusive_html_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = self.runtime.execute("/INTEL GENERATE DESIGN",
                request={"objective": "Dashboard", "format": "html"},
                authorization=CREATE, export_root=root, filename="preview.html")
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["manifest"].state.value, "exported")
            self.assertTrue(result["manifest"].output_verified)
            data = (root / "preview.html").read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), result["evidence"]["file_sha256"])
            duplicate = self.runtime.execute("/INTEL GENERATE DESIGN",
                request={"objective": "Dashboard", "format": "html"},
                authorization=CREATE, export_root=root, filename="preview.html")
            self.assertEqual(duplicate["error"]["code"], "DESTINATION_EXISTS")
            for name in ("../outside.html", "another/out.html", "bad.svg"):
                with self.subTest(name=name):
                    bad = self.runtime.execute("/INTEL GENERATE DESIGN",
                        request={"objective": "Dashboard", "format": "html"},
                        authorization=CREATE, export_root=root, filename=name)
                    self.assertFalse(bad["ok"])

    def test_cli_markdown_html_and_deny(self):
        with tempfile.TemporaryDirectory() as folder:
            cli = [sys.executable, "-m", "generators", "design", "--objective", "Analytics",
                   "--layout", "landing", "--format", "html",
                   "--export-root", folder, "--filename", "landing.html"]
            denied = subprocess.run(cli, capture_output=True, text=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)
            result = subprocess.run(cli + ["--authorize-create"],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((Path(folder)/"landing.html").read_text(), result.stdout)
 
    def test_mcp_design_tool_and_no_network(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 14)
        design = next(x for x in tools if x["name"] == "generate_design")
        self.assertEqual(design["inputSchema"]["required"], ["objective"])
        for fmt in ("markdown", "html"):
            answer = host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "generate_design", "arguments": {
                    "objective": "Landing for developers", "layout": "landing", "format": fmt}}})["result"]
            self.assertFalse(answer["isError"], answer)
            self.assertEqual(answer["structuredContent"]["capability"], "design")
            self.assertFalse(answer["structuredContent"]["output_verified"])
            self.assertEqual(answer["structuredContent"]["verification"]["browser_test"], "not_run")

    def test_invalid_html_validation(self):
        self.assertFalse(validate_html("<script>danger</script>")["no_scripts"])
        self.assertFalse(validate_html("<img src='https://example.com/x'>")["no_remote_assets"])


if __name__ == "__main__":
    unittest.main()
