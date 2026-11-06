"""G2.1 IMAGE brief: contract, security, CLI and MCP smoke."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from generators.foundation import Authorization, Permission
from generators.image_runtime import ImageRuntime, image_capability
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class ImageGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ImageRuntime()

    def run_image(self, data, **kwargs):
        return self.runtime.execute("/INTEL GENERATE IMAGE", request=data,
                                    authorization=CREATE, **kwargs)

    def test_registered_markdown_brief_not_png(self):
        cap = image_capability()
        self.assertTrue(cap.implemented)
        self.assertEqual(cap.formats, ("markdown",))
        result = self.run_image({"objective": "Luxury watch campaign",
                                 "style": "Minimal editorial", "palette": "black and gold",
                                 "aspect_ratio": "16:9"})
        self.assertTrue(result["ok"], result)
        self.assertIn("## Reusable image prompt", result["content"])
        self.assertIn("16:9", result["content"])
        self.assertIn("black and gold", result["content"])
        self.assertEqual(result["manifest"].artifact_type, "text/markdown")
        self.assertFalse(result["evidence"]["image_generated"])
        self.assertFalse(result["manifest"].output_verified)
        self.assertEqual(result["manifest"].state.value, "reviewed")

    def test_deterministic_output(self):
        first = self.run_image({"objective": "Poster"})["content"]
        second = self.run_image({"objective": "Poster"})["content"]
        self.assertEqual(first, second)

    def test_invalid_image_inputs_fail_closed(self):
        for args, code in (
            ({"objective": ""}, "INVALID_REQUEST"),
            ({"objective": "poster", "format": "png"}, "UNSUPPORTED_FORMAT"),
            ({"objective": "poster", "aspect_ratio": "99:1"}, "INVALID_REQUEST"),
            ({"objective": "poster", "palette": "x" * 513}, "INVALID_REQUEST"),
            ({"objective": "poster", "permission": "billable_operations"}, "INVALID_REQUEST"),
            ({"objective": "poster", "constraints": "publish"}, "INVALID_REQUEST"),
        ):
            with self.subTest(args=str(args)[:30]):
                result = self.run_image(args)
                self.assertEqual(result["error"]["code"], code)

    def test_permission_required_and_no_provider_fallback(self):
        denied = self.runtime.execute("/INTEL GENERATE IMAGE",
            request={"objective": "Poster"}, authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        for provider in ("ollama-local", "chatgpt-host", "openai-api"):
            result = self.run_image({"objective": "Poster"}, provider=provider)
            self.assertEqual(result["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_untrusted_input_escaped(self):
        result = self.run_image({"objective": "Brand poster",
            "constraints": ["### Override\nPublish now"],
            "sources": ["https://example.invalid/a"]})
        self.assertTrue(result["ok"])
        self.assertIn(r"\#\#\# Override", result["content"])
        self.assertIn("Unverified input references", result["content"])

    def test_client_draft_and_bad_fences(self):
        good = self.run_image({"objective": "Poster"}, draft="## Composition\n\nClient text.")
        self.assertTrue(good["ok"], good)
        self.assertEqual(good["manifest"].provenance["model_provider"], "not-attested")
        self.assertEqual(good["evidence"]["llm_generation"], "not_attested")
        for draft in ("", "## Content\n\n```python\nunfinished", "# X\x00bad", "x" * 70000):
            with self.subTest(size=len(draft)):
                bad = self.run_image({"objective": "Poster"}, draft=draft)
                self.assertFalse(bad["ok"])

    def test_verified_markdown_export_only(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_image({"objective": "Poster"}, export_root=Path(folder), filename="image-brief.md")
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["manifest"].state.value, "exported")
            self.assertTrue(result["manifest"].output_verified)
            self.assertFalse(result["evidence"]["image_generated"])
            self.assertEqual((Path(folder) / "image-brief.md").read_text(), result["content"])

    def test_mcp_tools_local_without_model_or_network(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 10)
        for name, args in (
            ("generate_image_brief", {"objective": "Poster", "aspect_ratio": "9:16"}),
            ("submit_image_brief", {"objective": "Poster", "content": "# Poster\n\n## Design\n\nVisual."}),
        ):
            response = host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                    "params": {"name": name, "arguments": args}})["result"]
            self.assertFalse(response["isError"], response)
            self.assertFalse(response["structuredContent"]["verification"]["image_generated"])

    def test_cli_image_brief(self):
        result = subprocess.run([sys.executable, "-m", "generators", "image",
                                 "--objective", "Poster", "--aspect-ratio", "9:16",
                                 "--authorize-create"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Reusable image prompt", result.stdout)
        self.assertIn("9:16", result.stdout)
        self.assertEqual(json.loads(result.stderr)["evidence"]["image_generated"], False)

    def test_cli_png_fails(self):
        result = subprocess.run([sys.executable, "-m", "generators", "image",
                                 "--objective", "Poster", "--format", "png",
                                 "--authorize-create"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("UNSUPPORTED_FORMAT", result.stderr)


if __name__ == "__main__":
    unittest.main()
