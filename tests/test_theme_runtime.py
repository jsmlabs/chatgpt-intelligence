"""G2.3 THEME deterministic token, CSS, contrast and integration regression."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from generators.foundation import Authorization, Permission
from generators.theme_runtime import (
    ThemeRuntime, theme_capability, relative_luminance, contrast_ratio,
    hex_color, palette_for, audit, validate_output, export_theme,
)
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ThemeRuntime()

    def run_theme(self, **kwargs):
        return self.runtime.execute("/INTEL GENERATE THEME",
            request={"objective": "Secure financial dashboard", **kwargs},
            authorization=CREATE)

    def test_w3c_reference_pairs_and_luminance(self):
        self.assertAlmostEqual(relative_luminance("#000000"), 0.0)
        self.assertAlmostEqual(relative_luminance("#ffffff"), 1.0)
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0)
        self.assertAlmostEqual(contrast_ratio("#ffffff", "#000000"), 21.0)
        self.assertAlmostEqual(contrast_ratio("#777777", "#FFFFFF"), 4.478, places=2)
        self.assertEqual(hex_color("#00aAbB"), "#00AABB")

    def test_presets_and_audited_pairs(self):
        for preset in ("graphite", "ocean", "plum", "forest"):
            with self.subTest(preset=preset):
                result = self.run_theme(preset=preset)
                self.assertTrue(result["ok"], result)
                payload = json.loads(result["content"])
                contrast = payload["contrast_audit"]
                self.assertTrue(contrast["aa_passed"])
                self.assertTrue(contrast["aaa_text_background_passed"])
                self.assertEqual(len(contrast["pair_results"]), 24)
                self.assertTrue(all(row["passed"] for row in contrast["pair_results"]))
                self.assertEqual(set(payload["tokens"]), {"light", "dark"})
                self.assertEqual(payload["tokens"]["light"]["color"]["accent"]["$type"], "color")
                self.assertEqual(result["manifest"].artifact_type, "application/json")
                self.assertFalse(result["manifest"].output_verified)
                self.assertEqual(result["evidence"]["accessibility_certification"], "not_run")

    def test_custom_accents_and_ink_contrast(self):
        for accent in ("#000000", "#FFFFFF", "#777777", "#00FF00", "#FF00FF", "#ee9933"):
            with self.subTest(accent=accent):
                result = self.run_theme(accent=accent)
                self.assertTrue(result["ok"], result)
                value = json.loads(result["content"])
                for mode in ("light", "dark"):
                    colors = value["tokens"][mode]["color"]
                    self.assertEqual(colors["accent"]["$value"], accent.upper())
                    self.assertGreaterEqual(contrast_ratio(
                        colors["on_accent"]["$value"], colors["accent"]["$value"]), 4.5)

    def test_deterministic_output(self):
        a = self.run_theme(preset="forest")["content"]
        b = self.run_theme(preset="forest")["content"]
        self.assertEqual(a, b)

    def test_css_modes_and_no_remote_import(self):
        result = self.run_theme(format="css", preset="ocean")
        self.assertTrue(result["ok"], result)
        css = result["content"]
        self.assertIn('data-theme="light"', css)
        self.assertIn('data-theme="dark"', css)
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn("--intel-on-accent:", css)
        self.assertTrue(all(validate_output(css, "css").values()))
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)
        self.assertEqual(result["manifest"].artifact_type, "text/css")

    def test_rejected_inputs_fail_closed(self):
        for payload, code in (
            ({"objective": ""}, "INVALID_REQUEST"),
            ({"preset": "unknown"}, "INVALID_REQUEST"),
            ({"accent": "#abcd"}, "INVALID_REQUEST"),
            ({"accent": "red;url(https://evil.invalid)"}, "INVALID_REQUEST"),
            ({"accent": "#12345678"}, "INVALID_REQUEST"),
            ({"format": "svg"}, "UNSUPPORTED_FORMAT"),
            ({"permission": "billable_operations"}, "INVALID_REQUEST"),
            ({"objective": "bad\x00token"}, "INVALID_REQUEST"),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_theme(**payload)["error"]["code"], code)
        denied = self.runtime.execute("/INTEL GENERATE THEME",
            request={"objective": "Test"}, authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        billable = self.runtime.execute("/INTEL GENERATE THEME",
            request={"objective": "Test"}, authorization=CREATE, provider="openai-api")
        self.assertEqual(billable["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_export_json_css_exclusive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for fmt in ("json", "css"):
                result = self.runtime.execute("/INTEL GENERATE THEME",
                    request={"objective": "Example", "format": fmt},
                    authorization=CREATE, export_root=root, filename="theme." + fmt)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["manifest"].state.value, "exported")
                self.assertTrue(result["manifest"].output_verified)
                content = (root / ("theme." + fmt)).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), result["evidence"]["file_sha256"])
                duplicate = self.runtime.execute("/INTEL GENERATE THEME",
                    request={"objective": "Example", "format": fmt},
                    authorization=CREATE, export_root=root, filename="theme." + fmt)
                self.assertEqual(duplicate["error"]["code"], "DESTINATION_EXISTS")
            for name in ("../oops.json", "nested/file.json", "bad.css", "C:/oops.json"):
                with self.subTest(name=name):
                    result = self.runtime.execute("/INTEL GENERATE THEME",
                        request={"objective": "Example"}, authorization=CREATE,
                        export_root=root, filename=name)
                    self.assertFalse(result["ok"])

    def test_cli_format_and_deny(self):
        with tempfile.TemporaryDirectory() as folder:
            base = [sys.executable, "-m", "generators", "theme",
                    "--objective", "Dashboard", "--preset", "plum", "--format", "css",
                    "--export-root", folder, "--filename", "theme.css"]
            denied = subprocess.run(base, capture_output=True, text=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)
            allowed = subprocess.run(base + ["--authorize-create"],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertEqual(allowed.stdout, (Path(folder) / "theme.css").read_text())
            evidence = json.loads(allowed.stderr)["evidence"]
            self.assertTrue(evidence["contrast_audit"]["aa_passed"])

    def test_cli_default_json_preserves_existing_markdown_defaults(self):
        generated = subprocess.run(
            [sys.executable, "-m", "generators", "theme", "--objective", "Tokens",
             "--authorize-create"], capture_output=True, text=True, timeout=15)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.assertEqual(json.loads(generated.stdout)["capability"], "theme")
        legacy = subprocess.run(
            [sys.executable, "-m", "generators", "design", "--objective", "Layout",
             "--authorize-create"], capture_output=True, text=True, timeout=15)
        self.assertEqual(legacy.returncode, 0, legacy.stderr)
        self.assertTrue(legacy.stdout.startswith("# Design Specification"))

    def test_mcp_tool_contract_and_permissions(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 12)
        schema = next(x for x in tools if x["name"] == "generate_theme")["inputSchema"]
        self.assertEqual(schema["required"], ["objective"])
        for fmt in ("json", "css"):
            output = host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "generate_theme", "arguments": {
                    "objective": "Finance", "preset": "graphite", "format": fmt}}})["result"]
            self.assertFalse(output["isError"], output)
            self.assertEqual(output["structuredContent"]["capability"], "theme")
            self.assertFalse(output["structuredContent"]["output_verified"])
            self.assertTrue(output["structuredContent"]["verification"]["contrast_audit"]["aa_passed"])
        bad = host.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "generate_theme", "arguments": {
                "objective": "Finance", "unknown": True}}})
        self.assertEqual(bad["error"]["code"], -32602)
        denied_host = MCPHost(Authorization())
        denied_host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        denied = denied_host.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "generate_theme", "arguments": {"objective": "Finance"}}})["result"]
        self.assertTrue(denied["isError"])
        self.assertIn("PERMISSION_DENIED", denied["content"][0]["text"])

    def test_non_text_contrast_is_not_text_contrast(self):
        report = audit(palette_for("#5566EE"))
        checks = {(r["foreground"], r["background"], r["criterion"]): r
                  for r in report["pair_results"] if r["mode"] == "light"}
        self.assertEqual(checks[("border", "surface", "non_text_aa")]["minimum"], 3.0)
        self.assertEqual(checks[("text", "surface", "normal_text_aa")]["minimum"], 4.5)


if __name__ == "__main__":
    unittest.main()
