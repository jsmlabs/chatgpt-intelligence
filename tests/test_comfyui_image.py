"""G2.1.2 ComfyUI local-only provider protocol and safety tests."""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from uuid import UUID

from generators.comfyui_image import (
    ComfyImage, ComfyUIHost, _workflow, export_comfy_image, verify_png,
)
from generators.foundation import Authorization, IntelError, Permission
from generators.image_render import render_abstract_png, _chunk, PNG_SIGNATURE
import struct
import zlib
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))
LOCAL = Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL}))
PROMPT_ID = "44ebee35-0c62-4b26-9b05-c9b54161a355"
MODEL = "local-test.safetensors"


class HTTPResponse:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size):
        return self.body[:size]


class FakeHTTP:
    def __init__(self, *, png=None, installed=True, history_status="success"):
        self.requests = []
        self.png = png if png is not None else render_abstract_png("local-model-fixture")
        self.installed = installed
        self.history_status = history_status

    def open(self, request, timeout):
        self.requests.append((request.full_url, request))
        path = request.full_url.removeprefix("http://127.0.0.1:8188")
        if path == "/models/checkpoints":
            return HTTPResponse([MODEL] if self.installed else [])
        if path == "/prompt":
            return HTTPResponse({"prompt_id": PROMPT_ID, "node_errors": {}})
        if path == "/history/" + PROMPT_ID:
            return HTTPResponse({
                PROMPT_ID: {
                    "status": {"status_str": self.history_status, "completed": True},
                    "outputs": {"9": {"images": [{"filename": "INTEL_00001.png",
                                                  "subfolder": "", "type": "output"}]}}
                }
            })
        if path.startswith("/view?"):
            return HTTPResponse(self.png)
        raise AssertionError("Unexpected HTTP path " + path)


class ComfyUITests(unittest.TestCase):
    def test_realistic_local_protocol_and_allowed_nodes(self):
        fake = FakeHTTP()
        host = ComfyUIHost(checkpoint=MODEL, opener=fake)
        image = host.generate("a glowing mountain landscape", authorization=LOCAL,
                              width=384, height=384, steps=12, seed=7)
        self.assertEqual(image.provider, "comfyui-local")
        self.assertEqual(image.sha256, hashlib.sha256(image.png).hexdigest())
        self.assertEqual(image.prompt_id, PROMPT_ID)
        self.assertEqual(verify_png(image.png), (384, 384))
        urls = [url for url, _ in fake.requests]
        self.assertEqual(len(urls), 4)
        self.assertEqual(urls[0], "http://127.0.0.1:8188/models/checkpoints")
        self.assertTrue(urls[3].startswith("http://127.0.0.1:8188/view?"))
        payload = json.loads(fake.requests[1][1].data)
        graph = payload["prompt"]
        self.assertEqual({node["class_type"] for node in graph.values()},
                         {"KSampler", "CheckpointLoaderSimple", "EmptyLatentImage",
                          "CLIPTextEncode", "VAEDecode", "SaveImage"})
        self.assertEqual(graph["6"]["inputs"]["text"], "a glowing mountain landscape")
        self.assertEqual(graph["3"]["inputs"]["steps"], 12)
        self.assertEqual(graph["4"]["inputs"]["ckpt_name"], MODEL)

    def test_grants_fail_closed_before_http(self):
        fake = FakeHTTP()
        host = ComfyUIHost(checkpoint=MODEL, opener=fake)
        for grant in (Authorization(), CREATE):
            with self.subTest(grant=grant), self.assertRaises(IntelError) as cm:
                host.generate("test", authorization=grant)
            self.assertEqual(cm.exception.code, "PERMISSION_DENIED")
        self.assertEqual(fake.requests, [])

    def test_checkpoint_must_be_configured_and_installed(self):
        fake = FakeHTTP()
        with self.assertRaises(IntelError) as cm:
            ComfyUIHost(checkpoint="", opener=fake).generate("test", authorization=LOCAL)
        self.assertEqual(cm.exception.code, "MODEL_UNAVAILABLE")
        self.assertEqual(fake.requests, [])
        fake = FakeHTTP(installed=False)
        with self.assertRaises(IntelError) as cm:
            ComfyUIHost(checkpoint=MODEL, opener=fake).generate("test", authorization=LOCAL)
        self.assertEqual(cm.exception.code, "MODEL_UNAVAILABLE")
        self.assertEqual(len(fake.requests), 1)

    def test_invalid_inputs_no_queue(self):
        for overrides in ({"width": 255}, {"width": True}, {"steps": 41},
                          {"height": 1000}, {"seed": -1}, {"negative_prompt": "x" * 1025},
                          {"prompt": ""}):
            fake = FakeHTTP()
            host = ComfyUIHost(checkpoint=MODEL, opener=fake)
            kwargs = {"prompt": "test", "authorization": LOCAL}
            kwargs.update(overrides)
            with self.subTest(overrides=str(overrides)[:45]), self.assertRaises(IntelError):
                host.generate(**kwargs)
            self.assertEqual(fake.requests, [])

    def test_history_failure(self):
        fake = FakeHTTP(history_status="error")
        with self.assertRaises(IntelError) as cm:
            ComfyUIHost(checkpoint=MODEL, opener=fake).generate(
                "test", authorization=LOCAL, width=384, height=384)
        self.assertEqual(cm.exception.code, "MODEL_REQUEST_FAILED")

    def test_png_rejection(self):
        valid = render_abstract_png("test")
        for png in (valid[:-12], valid + b"TRAIL", valid[:50] + b"x" + valid[51:]):
            with self.subTest(len=len(png)), self.assertRaises(IntelError):
                verify_png(png)
        fake = FakeHTTP(png=valid[:-5])
        with self.assertRaises(IntelError) as cm:
            ComfyUIHost(checkpoint=MODEL, opener=fake).generate(
                "test", authorization=LOCAL, width=384, height=384)
        self.assertEqual(cm.exception.code, "IMAGE_INVALID")

    def test_compressed_pixel_data_checked(self):
        valid = render_abstract_png("test")
        # Keep chunks and CRC valid but replace IDAT with a truncated zlib stream.
        start = 8 + 25
        size = struct.unpack_from("!I", valid, start)[0]
        end = start + 12 + size
        damaged = valid[:start] + _chunk(b"IDAT", zlib.compress(b"short")) + valid[end:]
        with self.assertRaises(IntelError) as err:
            verify_png(damaged)
        self.assertEqual(err.exception.code, "IMAGE_INVALID")

        # Extra decompressed bytes must be rejected without allocating unbounded data.
        width, height = 384, 384
        raw = bytes([0]) + bytes(width * 3)
        inflated = zlib.compress(raw * height + b"unexpected-extra")
        oversized = valid[:start] + _chunk(b"IDAT", inflated) + valid[end:]
        with self.assertRaises(IntelError):
            verify_png(oversized)

    def test_no_redirects_and_proxy(self):
        opener = ComfyUIHost(checkpoint=MODEL).opener
        self.assertTrue(any(type(x).__name__ == "NoRedirect" for x in opener.handlers))
        # An explicit empty ProxyHandler suppresses urllib's default proxy handler.
        self.assertFalse(any(type(x).__name__ == "ProxyHandler" for x in opener.handlers))

    def test_export_exclusive_and_source_integrity(self):
        png = render_abstract_png("test")
        image = ComfyImage(png, 384, 384, hashlib.sha256(png).hexdigest(),
                           MODEL, PROMPT_ID)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(export_comfy_image(image, root, "photo.png"), "photo.png")
            self.assertEqual((root / "photo.png").read_bytes(), png)
            with self.assertRaises(IntelError) as exists:
                export_comfy_image(image, root, "photo.png")
            self.assertEqual(exists.exception.code, "DESTINATION_EXISTS")
            for name in ("../escape.png", "nested/out.png", "photo.jpg", "C:/oops.png"):
                with self.assertRaises(IntelError):
                    export_comfy_image(image, root, name)

    def test_cli_defaults_to_permission_denial(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([
                sys.executable, "-m", "generators.comfyui_image",
                "--prompt", "a mountain", "--checkpoint", MODEL,
                "--export-root", folder, "--filename", "test.png",
            ], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn("PERMISSION_DENIED", result.stderr)
            self.assertFalse((Path(folder) / "test.png").exists())

    def test_mcp_opt_in_and_image_response(self):
        fake = FakeHTTP()
        comfy = ComfyUIHost(checkpoint=MODEL, opener=fake)
        def init(host):
            host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            return host
        closed = init(MCPHost(CREATE, comfyui_host=comfy))
        names = [x["name"] for x in closed.handle({
            "jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]]
        self.assertNotIn("generate_image_comfyui", names)
        enabled = init(MCPHost(CREATE, allow_comfyui_image=True, comfyui_host=comfy))
        names = [x["name"] for x in enabled.handle({
            "jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]]
        self.assertEqual(len(names), 11)
        response = enabled.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "generate_image_comfyui", "arguments": {
                "prompt": "a mountain", "width": 384, "height": 384}}})["result"]
        self.assertFalse(response["isError"], response)
        self.assertEqual(response["structuredContent"]["model_provider"], "comfyui-local")
        raw = base64.b64decode(response["content"][0]["data"])
        self.assertEqual(verify_png(raw), (384, 384))
        self.assertFalse(response["structuredContent"]["output_verified"])

    def test_mcp_permission_without_model_request(self):
        fake = FakeHTTP()
        enabled = MCPHost(Authorization(), allow_comfyui_image=True,
                          comfyui_host=ComfyUIHost(checkpoint=MODEL, opener=fake))
        enabled.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        result = enabled.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "generate_image_comfyui", "arguments": {
                "prompt": "test"}}})["result"]
        self.assertTrue(result["isError"])
        self.assertIn("PERMISSION_DENIED", result["content"][0]["text"])
        self.assertEqual(fake.requests, [])


if __name__ == "__main__":
    unittest.main()
