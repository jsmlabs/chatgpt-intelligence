"""G3.2 SLIDES export and protocol regression tests."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from generators.foundation import Authorization, Permission, IntelError
from generators.slides_runtime import SlidesRuntime, slide_capability, verify_pptx
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class SlidesTests(unittest.TestCase):
    def setUp(self):
        self.runtime = SlidesRuntime()

    def make(self, **kwargs):
        return self.runtime.execute("/INTEL GENERATE SLIDES", authorization=CREATE,
            request={"objective": "Research dashboard", **kwargs})

    def test_json_outline_and_capability(self):
        self.assertEqual(slide_capability().formats, ("json", "pptx"))
        result = self.make()
        self.assertTrue(result["ok"], result)
        data = json.loads(result["content"])
        self.assertEqual(len(data["slides"]), 3)
        self.assertEqual(data["canvas"]["aspect_ratio"], "16:9")
        self.assertTrue(data["theme"]["contrast_audit"]["aa_passed"])
        self.assertFalse(result["manifest"].output_verified)

    def test_pptx_editable_text_and_layouts(self):
        slides = [
            {"layout": "title", "title": "Introduction", "body": ["Audience"]},
            {"layout": "section", "title": "Context", "body": ["Purpose"]},
            {"layout": "bullets", "title": "Results", "body": ["First", "Second"]},
            {"layout": "two-column", "title": "Compare", "body": ["Left", "Right"]},
        ]
        out = self.make(format="pptx", slides=slides)
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["evidence"]["slide_count"], 4)
        self.assertEqual(out["manifest"].artifact_type,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        with ZipFile(io.BytesIO(out["content"])) as z:
            self.assertIsNone(z.testzip())
            self.assertIn("ppt/theme/theme1.xml", z.namelist())
            self.assertIn(b"First", z.read("ppt/slides/slide3.xml"))
            self.assertIn(b"Second", z.read("ppt/slides/slide3.xml"))
            self.assertEqual(len([name for name in z.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")]), 4)

    def test_determinism_and_escaping(self):
        req = {"format": "pptx", "slides": [
            {"layout": "title", "title": '<script>& invalid', "body": ['<xml>']}]}
        a, b = self.make(**req), self.make(**req)
        self.assertTrue(a["ok"], a)
        self.assertEqual(a["content"], b["content"])
        with ZipFile(io.BytesIO(a["content"])) as z:
            slide = z.read("ppt/slides/slide1.xml")
            self.assertIn(b"&lt;script&gt;", slide)
            self.assertNotIn(b"<script>", slide)
            for name in z.namelist():
                if name.endswith(".rels"):
                    self.assertNotIn(b'TargetMode="External"', z.read(name))

    def test_invalid_inputs_and_permissions(self):
        for payload, code in (
            ({"objective": ""}, "INVALID_REQUEST"),
            ({"format": "pdf"}, "UNSUPPORTED_FORMAT"),
            ({"preset": "unknown"}, "INVALID_REQUEST"),
            ({"accent": "red"}, "INVALID_REQUEST"),
            ({"slides": []}, "INVALID_REQUEST"),
            ({"slides": [{"title": "x"}] * 13}, "INVALID_REQUEST"),
            ({"slides": [{"layout": "two-column", "title": "x", "body": ["one"]}]}, "INVALID_REQUEST"),
            ({"slides": [{"layout": "title", "title": "bad\nline"}]}, "INVALID_REQUEST"),
            ({"slides": [{"layout": "title", "title": "ok", "body": ["x"]*7}]}, "INVALID_REQUEST"),
            ({"elevated": True}, "INVALID_REQUEST"),
        ):
            with self.subTest(payload=repr(payload)[:60]):
                self.assertEqual(self.make(**payload)["error"]["code"], code)
        denied = self.runtime.execute("/INTEL GENERATE SLIDES",
            request={"objective": "Test"}, authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        remote = self.runtime.execute("/INTEL GENERATE SLIDES",
            request={"objective": "Test"}, authorization=CREATE, provider="openai-api")
        self.assertEqual(remote["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_corrupted_zip_and_mismatched_story(self):
        story = json.loads(self.make()["content"])
        pptx = self.make(format="pptx")["content"]
        self.assertTrue(verify_pptx(pptx, story)["pptx_verified"])
        with self.assertRaises(IntelError):
            verify_pptx(b"not a zip", story)
        with self.assertRaises(IntelError):
            verify_pptx(pptx, {**story, "slides": story["slides"][:-1]})

    def test_exclusive_verified_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for fmt in ("json", "pptx"):
                filename = "deck." + fmt
                out = self.runtime.execute("/INTEL GENERATE SLIDES",
                    request={"objective": "Test", "format": fmt},
                    authorization=CREATE, export_root=root, filename=filename)
                self.assertTrue(out["ok"], out)
                self.assertTrue(out["manifest"].output_verified)
                self.assertEqual(out["manifest"].state.value, "exported")
                self.assertEqual(hashlib.sha256((root/filename).read_bytes()).hexdigest(),
                                 out["evidence"]["file_sha256"])
                again = self.runtime.execute("/INTEL GENERATE SLIDES",
                    request={"objective": "Test", "format": fmt},
                    authorization=CREATE, export_root=root, filename=filename)
                self.assertEqual(again["error"]["code"], "DESTINATION_EXISTS")
            for name in ("../bad.pptx", "sub/deck.pptx", "bad.txt", "C:/deck.pptx"):
                out = self.runtime.execute("/INTEL GENERATE SLIDES",
                    request={"objective": "Test", "format": "pptx"},
                    authorization=CREATE, export_root=root, filename=name)
                self.assertFalse(out["ok"])

    def test_cli_json_and_pptx(self):
        with tempfile.TemporaryDirectory() as folder:
            args = [sys.executable, "-m", "generators", "slides", "--objective", "Roadmap"]
            outline = subprocess.run(args + ["--authorize-create"], text=True,
                                     capture_output=True, timeout=15)
            self.assertEqual(outline.returncode, 0, outline.stderr)
            self.assertEqual(len(json.loads(outline.stdout)["slides"]), 3)
            pptx = subprocess.run(args + ["--authorize-create", "--format", "pptx",
                "--slide", "title|Welcome|Summary",
                "--slide", "bullets|Plan|Build|Verify",
                "--export-root", folder, "--filename", "slides.pptx"],
                text=True, capture_output=True, timeout=15)
            self.assertEqual(pptx.returncode, 0, pptx.stderr)
            self.assertEqual(json.loads(pptx.stdout)["slide_count"], 2)
            self.assertTrue((Path(folder)/"slides.pptx").is_file())
            denied = subprocess.run(args + ["--format", "pptx", "--export-root", folder,
                "--filename", "denied.pptx"], text=True, capture_output=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)

    def test_mcp_json_and_binary(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 14)
        self.assertIn("generate_slides", [x["name"] for x in tools])
        def call(fmt):
            return host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "generate_slides", "arguments": {
                    "objective": "Roadmap", "format": fmt}}})["result"]
        js, binary = call("json"), call("pptx")
        self.assertFalse(js["isError"], js)
        self.assertEqual(len(json.loads(js["content"][0]["text"])["slides"]), 3)
        self.assertFalse(binary["isError"], binary)
        content = binary["structuredContent"]
        self.assertFalse(content["output_verified"])
        self.assertEqual(content["verification"]["slide_count"], 3)
        self.assertTrue(base64.b64decode(content["base64"], validate=True).startswith(b"PK"))
        denied = MCPHost(Authorization())
        denied.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        refusal = denied.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "generate_slides",
                       "arguments": {"objective": "Denied"}}})["result"]
        self.assertTrue(refusal["isError"])


if __name__ == "__main__":
    unittest.main()
