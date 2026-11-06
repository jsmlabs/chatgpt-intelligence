"""G3.1 procedural GIF, actual frame checks, storyboard, CLI and MCP."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from generators.foundation import Authorization, Permission
from generators.motion_runtime import MotionRuntime, motion_capability, verify_gif
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.runtime = MotionRuntime()

    def run_motion(self, **options):
        return self.runtime.execute("/INTEL GENERATE GIF",
            authorization=CREATE, request={"objective": "Looping abstract indicator", **options})

    def test_capability_and_storyboard(self):
        cap = motion_capability()
        self.assertEqual(cap.formats, ("json", "gif"))
        result = self.run_motion(motion="orbit", frames=6, frame_duration_ms=150, loop=2)
        self.assertTrue(result["ok"], result)
        story = json.loads(result["content"])
        self.assertEqual(story["capability"], "motion")
        self.assertEqual(story["timing"]["frames"], 6)
        self.assertEqual(story["timing"]["total_duration_ms"], 900)
        self.assertEqual(story["timing"]["loop"], 2)
        self.assertEqual(len(story["frames"]), 6)
        self.assertEqual([f["time_ms"] for f in story["frames"]],
                         [0, 150, 300, 450, 600, 750])
        self.assertFalse(result["evidence"]["gif_generated"])
        self.assertFalse(result["manifest"].output_verified)

    def test_three_motion_styles_generate_verifiable_frames(self):
        for motion in ("pulse", "orbit", "bounce"):
            with self.subTest(motion=motion):
                result = self.run_motion(format="gif", motion=motion, width=64,
                    height=80, frames=4, frame_duration_ms=80, loop=0)
                self.assertTrue(result["ok"], result)
                gif = result["content"]
                self.assertIsInstance(gif, bytes)
                self.assertTrue(gif.startswith(b"GIF89a"))
                actual = verify_gif(gif, width=64, height=80, frames=4,
                                    duration_ms=80, loop=0)
                self.assertEqual(actual["decoded_frames"], 4)
                self.assertEqual(actual["sha256"], hashlib.sha256(gif).hexdigest())
                self.assertTrue(result["evidence"]["gif_verified"])
                self.assertEqual(result["evidence"]["frame_count"], 4)
                self.assertFalse(result["manifest"].output_verified)

    def test_distinct_frames_and_reproducibility(self):
        from generators.motion_runtime import pixels
        for motion in ("pulse", "orbit", "bounce"):
            images = [pixels(128, 128, motion, i / 8) for i in range(8)]
            self.assertGreater(len(set(images)), 1, motion)
            self.assertEqual(images[0], pixels(128, 128, motion, 1.0))
        a = self.run_motion(format="gif", motion="orbit", frames=3, width=64, height=64)["content"]
        b = self.run_motion(format="gif", motion="orbit", frames=3, width=64, height=64)["content"]
        self.assertEqual(a, b)

    def test_timing_loop_trailer_corruption_detected(self):
        from generators.foundation import IntelError
        result = self.run_motion(format="gif", width=64, height=64,
                                 frames=3, frame_duration_ms=100, loop=3)
        self.assertTrue(result["ok"], result)
        data = result["content"]
        verify_gif(data, width=64, height=64, frames=3, duration_ms=100, loop=3)
        for damaged in (data[:-1], data + b"x", data.replace(b"GIF89a", b"BAD89a", 1),
                        data.replace(b"NETSCAPE2.0", b"NETSCAPE2.X", 1)):
            with self.subTest(damage=len(damaged)):
                with self.assertRaises(IntelError):
                    verify_gif(damaged, width=64, height=64,
                               frames=3, duration_ms=100, loop=3)
        with self.assertRaises(IntelError):
            verify_gif(data, width=64, height=64, frames=4, duration_ms=100, loop=3)
        with self.assertRaises(IntelError):
            verify_gif(data, width=64, height=64, frames=3, duration_ms=200, loop=3)
        with self.assertRaises(IntelError):
            verify_gif(data, width=64, height=64, frames=3, duration_ms=100, loop=0)

    def test_limits_and_invalid_inputs(self):
        cases = [
            ({"objective": ""}, "INVALID_REQUEST"),
            ({"motion": "spin"}, "INVALID_REQUEST"),
            ({"width": 16}, "INVALID_REQUEST"),
            ({"height": 257}, "INVALID_REQUEST"),
            ({"frames": 1}, "INVALID_REQUEST"),
            ({"frames": 13}, "INVALID_REQUEST"),
            ({"frames": True}, "INVALID_REQUEST"),
            ({"frame_duration_ms": 55}, "INVALID_REQUEST"),
            ({"frame_duration_ms": 0}, "INVALID_REQUEST"),
            ({"loop": -1}, "INVALID_REQUEST"),
            ({"loop": 21}, "INVALID_REQUEST"),
            ({"accent": "red"}, "INVALID_REQUEST"),
            ({"format": "mp4"}, "UNSUPPORTED_FORMAT"),
            ({"authorize_billable": True}, "INVALID_REQUEST"),
        ]
        for kwargs, code in cases:
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.run_motion(**kwargs)["error"]["code"], code)

    def test_default_denied_and_no_external_provider(self):
        blocked = self.runtime.execute("/INTEL GENERATE GIF",
            request={"objective": "Loading"}, authorization=Authorization())
        self.assertEqual(blocked["error"]["code"], "PERMISSION_DENIED")
        paid = self.runtime.execute("/INTEL GENERATE GIF",
            request={"objective": "Loading"}, authorization=CREATE, provider="openai-api")
        self.assertEqual(paid["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_exclusive_gif_and_json_export(self):
        with tempfile.TemporaryDirectory() as folder:
            for fmt in ("gif", "json"):
                filename = "motion." + fmt
                output = self.runtime.execute("/INTEL GENERATE GIF",
                    request={"objective": "Indicator", "format": fmt, "frames": 3,
                             "width": 64, "height": 64},
                    authorization=CREATE, export_root=Path(folder), filename=filename)
                self.assertTrue(output["ok"], output)
                self.assertEqual(output["manifest"].state.value, "exported")
                self.assertTrue(output["manifest"].output_verified)
                stored = (Path(folder)/filename).read_bytes()
                self.assertEqual(hashlib.sha256(stored).hexdigest(),
                                 output["evidence"]["file_sha256"])
                if fmt == "gif":
                    verify_gif(stored, width=64, height=64, frames=3,
                               duration_ms=120, loop=0)
                duplicate = self.runtime.execute("/INTEL GENERATE GIF",
                    request={"objective": "Indicator", "format": fmt, "frames": 3,
                             "width": 64, "height": 64},
                    authorization=CREATE, export_root=Path(folder), filename=filename)
                self.assertEqual(duplicate["error"]["code"], "DESTINATION_EXISTS")
            for filename in ("../hack.gif", "sub/out.gif", "test.mp4", "C:/out.gif"):
                result = self.runtime.execute("/INTEL GENERATE GIF",
                    request={"objective": "Indicator", "format": "gif",
                             "frames": 2, "width": 64, "height": 64},
                    authorization=CREATE, export_root=Path(folder), filename=filename)
                self.assertFalse(result["ok"])

    def test_cli_json_and_gif(self):
        with tempfile.TemporaryDirectory() as folder:
            cli = [sys.executable, "-m", "generators", "gif", "--objective",
                   "Loading", "--motion", "bounce", "--frames", "3",
                   "--width", "64", "--height", "64", "--authorize-create"]
            json_result = subprocess.run(cli, capture_output=True, text=True, timeout=15)
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            self.assertEqual(json.loads(json_result.stdout)["timing"]["frames"], 3)
            gif_result = subprocess.run(cli + ["--format", "gif",
                "--export-root", folder, "--filename", "indicator.gif"],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(gif_result.returncode, 0, gif_result.stderr)
            self.assertEqual(json.loads(gif_result.stdout)["artifact_type"], "image/gif")
            self.assertTrue((Path(folder)/"indicator.gif").is_file())
            denied = subprocess.run(cli[:-1] + ["--format", "gif",
                "--export-root", folder, "--filename", "denied.gif"],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)

    def test_mcp_storyboard_and_actual_image(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        names = [x["name"] for x in host.handle({"jsonrpc": "2.0", "id": 2,
                       "method": "tools/list"})["result"]["tools"]]
        self.assertEqual(len(names), 14)
        self.assertIn("generate_motion", names)
        def call(fmt):
            return host.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "generate_motion", "arguments": {
                    "objective": "Spinner", "format": fmt, "width": 64,
                    "height": 64, "frames": 3}}})["result"]
        json_response = call("json")
        self.assertFalse(json_response["isError"])
        self.assertEqual(json.loads(json_response["content"][0]["text"])["timing"]["frames"], 3)
        image_response = call("gif")
        self.assertFalse(image_response["isError"])
        self.assertEqual(image_response["content"][0]["mimeType"], "image/gif")
        gif = base64.b64decode(image_response["content"][0]["data"], validate=True)
        verify_gif(gif, width=64, height=64, frames=3, duration_ms=120, loop=0)
        self.assertFalse(image_response["structuredContent"]["output_verified"])
        blocked = MCPHost(Authorization())
        blocked.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        denied = blocked.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "generate_motion",
                       "arguments": {"objective": "Spinner"}}})["result"]
        self.assertTrue(denied["isError"])
        self.assertIn("PERMISSION_DENIED", denied["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
