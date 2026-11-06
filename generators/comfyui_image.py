"""G2.1.2 explicit, local-only semantic image generation using ComfyUI core nodes.

Not connected to ChatGPT's image generator. No new Python dependencies or
cloud API nodes. ComfyUI and a locally installed checkpoint are prerequisites.
All network requests target fixed loopback port 8188 with proxies and redirects
disabled. No automatic model downloads or retries of generation requests.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4
import zlib

from .foundation import Authorization, IntelError, Permission, safe_relative_path
from .text_runtime import _require_text

BASE = "http://127.0.0.1:8188"
MAX_JSON = 131072
MAX_IMAGE = 4 * 1024 * 1024
MAX_PIXELS = 1024 * 1024
CHECKPOINT = re.compile(r"^[A-Za-z0-9_ .()-]{1,128}\.safetensors$", re.I)
OUTPUT_FILE = re.compile(r"^[A-Za-z0-9_.-]{1,128}\.png$", re.I)
PNG = b"\x89PNG\r\n\x1a\n"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def verify_png(data: bytes) -> tuple[int, int]:
    """Bounded PNG structural/CRC validation; not full pixel or safety review."""
    if not isinstance(data, bytes) or len(data) < 60 or len(data) > MAX_IMAGE or not data.startswith(PNG):
        raise IntelError("IMAGE_INVALID", "PNG missing or exceeds size limit")
    offset, seen, dimensions, idat = 8, [], None, bytearray()
    channels = 0
    while offset + 12 <= len(data):
        length = struct.unpack_from("!I", data, offset)[0]
        if length > MAX_IMAGE or offset + 12 + length > len(data):
            raise IntelError("IMAGE_INVALID", "Invalid PNG chunk length")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from("!I", data, offset + 8 + length)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise IntelError("IMAGE_INVALID", "PNG CRC mismatch")
        if not re.fullmatch(rb"[A-Za-z]{4}", kind):
            raise IntelError("IMAGE_INVALID", "Invalid PNG chunk type")
        if kind == b"IHDR":
            if seen or length != 13:
                raise IntelError("IMAGE_INVALID", "Malformed PNG header")
            width, height, depth, color, compression, filt, interlace = struct.unpack("!IIBBBBB", payload)
            if (not 64 <= width <= 1024 or not 64 <= height <= 1024
                or width * height > MAX_PIXELS or depth != 8 or color not in (2, 6)
                or compression or filt or interlace):
                raise IntelError("IMAGE_INVALID", "Unsupported PNG dimensions or format")
            dimensions = (width, height)
            channels = 3 if color == 2 else 4
        elif kind == b"IDAT":
            if dimensions is None:
                raise IntelError("IMAGE_INVALID", "Missing PNG header")
            idat.extend(payload)
        elif kind == b"IEND":
            if length or not idat or dimensions is None or offset + 12 != len(data):
                raise IntelError("IMAGE_INVALID", "PNG terminator or pixel data invalid")
            width, height = dimensions
            stride = 1 + width * channels
            expected = height * stride
            try:
                decompressor = zlib.decompressobj()
                raw = decompressor.decompress(bytes(idat), expected + 1)
            except zlib.error:
                raise IntelError("IMAGE_INVALID", "PNG pixel stream invalid") from None
            if (len(raw) != expected or not decompressor.eof or
                    decompressor.unconsumed_tail or decompressor.unused_data or
                    any(raw[pos] not in (0, 1, 2, 3, 4) for pos in range(0, expected, stride))):
                raise IntelError("IMAGE_INVALID", "PNG pixels exceed limits or contain invalid filters")
            return dimensions
        elif kind[0] & 32 == 0:
            raise IntelError("IMAGE_INVALID", "Unknown critical PNG chunk")
        seen.append(kind)
        offset += length + 12
    raise IntelError("IMAGE_INVALID", "Missing PNG terminator")


@dataclass(frozen=True)
class ComfyImage:
    png: bytes
    width: int
    height: int
    sha256: str
    checkpoint: str
    prompt_id: str
    provider: str = "comfyui-local"
    mime_type: str = "image/png"


def _workflow(positive: str, negative: str, model: str,
              width: int, height: int, seed: int, steps: int) -> dict:
    """Trusted fixed graph of *core local* nodes. Never accept arbitrary workflow JSON."""
    return {
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": 7.0, "sampler_name": "euler",
            "scheduler": "normal", "denoise": 1.0, "model": ["4", 0],
            "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {
            "text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "filename_prefix": "INTEL", "images": ["8", 0]}},
    }


class ComfyUIHost:
    def __init__(self, *, checkpoint: str | None = None, timeout: float = 180.0,
                 opener=None, clock=None, sleep=None):
        self.checkpoint = checkpoint if checkpoint is not None else os.environ.get("INTEL_COMFYUI_CHECKPOINT", "")
        if not isinstance(self.checkpoint, str):
            raise ValueError("Invalid checkpoint configuration")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 10 <= timeout <= 300:
            raise ValueError("Timeout must be 10-300 seconds")
        self.timeout = float(timeout)
        self.opener = opener or urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect())
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep

    @property
    def configured(self) -> bool:
        return bool(CHECKPOINT.fullmatch(self.checkpoint))

    def _request(self, path: str, *, payload: dict | None = None,
                 limit: int = MAX_JSON) -> bytes:
        method = "POST" if payload is not None else "GET"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        if data is not None and len(data) > MAX_JSON:
            raise IntelError("INVALID_REQUEST", "Workflow exceeds transport limit")
        request = urllib.request.Request(BASE + path, data=data, method=method,
            headers={"Content-Type": "application/json"} if data is not None else {})
        try:
            with self.opener.open(request, timeout=min(self.timeout, 10.0)) as response:
                content = response.read(limit + 1)
                if len(content) > limit:
                    raise IntelError("MODEL_RESPONSE_INVALID", "Local server response too large")
                return content
        except IntelError:
            raise
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, ValueError):
            raise IntelError("LOCAL_IMAGE_UNAVAILABLE", "Local ComfyUI request failed") from None

    def _json(self, path: str, payload: dict | None = None) -> object:
        try:
            return json.loads(self._request(path, payload=payload).decode("utf-8"))
        except (UnicodeError, ValueError):
            raise IntelError("MODEL_RESPONSE_INVALID", "Local ComfyUI returned invalid JSON") from None

    def generate(self, prompt: str, *, authorization: Authorization | None,
                 negative_prompt: str = "", width: int = 512,
                 height: int = 512, steps: int = 20,
                 seed: int = 0) -> ComfyImage:
        (authorization or Authorization()).require(frozenset({Permission.CREATE, Permission.EXTERNAL}))
        positive = _require_text(prompt, "prompt", required=True, limit=4096)
        negative = _require_text(negative_prompt, "negative_prompt", limit=1024)
        if not self.configured:
            raise IntelError("MODEL_UNAVAILABLE", "Set INTEL_COMFYUI_CHECKPOINT to an installed local .safetensors model")
        if any(type(v) is not int for v in (width, height, steps, seed)):
            raise IntelError("INVALID_REQUEST", "Width, height, steps and seed must be integers")
        if (not 256 <= width <= 1024 or not 256 <= height <= 1024 or
            width % 64 or height % 64 or width * height > MAX_PIXELS or
            not 1 <= steps <= 40 or not 0 <= seed <= 2**32 - 1):
            raise IntelError("INVALID_REQUEST", "Invalid dimensions, steps or seed")
        installed = self._json("/models/checkpoints")
        if not isinstance(installed, list) or self.checkpoint not in installed:
            raise IntelError("MODEL_UNAVAILABLE", "Configured checkpoint is not installed in ComfyUI")
        graph = _workflow(positive, negative, self.checkpoint, width, height, seed, steps)
        response = self._json("/prompt", {"prompt": graph, "client_id": uuid4().hex})
        if (not isinstance(response, dict)
                or not isinstance(response.get("prompt_id"), str)
                or not re.fullmatch(r"[0-9a-fA-F-]{36}", response["prompt_id"])
                or response.get("node_errors")):
            raise IntelError("MODEL_RESPONSE_INVALID", "ComfyUI did not accept the local workflow")
        prompt_id = response["prompt_id"]
        deadline = self.clock() + self.timeout
        history = None
        while self.clock() < deadline:
            entries = self._json("/history/" + prompt_id)
            if not isinstance(entries, dict):
                raise IntelError("MODEL_RESPONSE_INVALID", "Invalid ComfyUI history response")
            history = entries.get(prompt_id)
            if history is not None:
                break
            self.sleep(1.0)
        if not isinstance(history, dict):
            raise IntelError("MODEL_TIMEOUT", "Local image generation did not finish before timeout; check ComfyUI queue")
        status = history.get("status")
        if not isinstance(status, dict) or status.get("status_str") != "success" or status.get("completed") is not True:
            raise IntelError("MODEL_REQUEST_FAILED", "ComfyUI generation was not successful")
        outputs = history.get("outputs")
        images = outputs.get("9", {}).get("images") if isinstance(outputs, dict) else None
        if not isinstance(images, list) or len(images) != 1 or not isinstance(images[0], dict):
            raise IntelError("MODEL_RESPONSE_INVALID", "Expected one saved image from trusted SaveImage node")
        entry = images[0]
        filename, subfolder, type_ = entry.get("filename"), entry.get("subfolder"), entry.get("type")
        if (not isinstance(filename, str) or not OUTPUT_FILE.fullmatch(filename)
                or subfolder != "" or type_ != "output"):
            raise IntelError("MODEL_RESPONSE_INVALID", "Unexpected image reference from ComfyUI")
        path = "/view?" + urllib.parse.urlencode({
            "filename": filename, "subfolder": "", "type": "output"})
        png = self._request(path, limit=MAX_IMAGE)
        actual_width, actual_height = verify_png(png)
        if (actual_width, actual_height) != (width, height):
            raise IntelError("IMAGE_INVALID", "Generated dimensions differ from request")
        return ComfyImage(png, actual_width, actual_height, hashlib.sha256(png).hexdigest(),
                          self.checkpoint, prompt_id)


def export_comfy_image(image: ComfyImage, root: Path, filename: str) -> str:
    relative = safe_relative_path(filename)
    if "/" in relative or not OUTPUT_FILE.fullmatch(relative):
        raise IntelError("INVALID_PATH", "Output must be a plain .png filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must be an existing non-symlink directory")
    if verify_png(image.png) != (image.width, image.height) or hashlib.sha256(image.png).hexdigest() != image.sha256:
        raise IntelError("IMAGE_INVALID", "Image integrity check failed")
    dest = root / relative
    if dest.is_symlink():
        raise IntelError("INVALID_PATH", "Output must not be a symlink")
    try:
        with dest.open("xb") as fp:
            fp.write(image.png)
            fp.flush()
            os.fsync(fp.fileno())
        if dest.read_bytes() != image.png:
            raise IntelError("EXPORT_UNVERIFIED", "Export verification failed")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite an existing file") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Local PNG export failed") from None
    except IntelError:
        try:
            dest.unlink()
        except OSError:
            pass
        raise
    return relative


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Explicit local ComfyUI image generation (no cloud API)")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--authorize-create", action="store_true")
    parser.add_argument("--authorize-local-inference", action="store_true")
    args = parser.parse_args(argv)
    auth = Authorization(frozenset(
        ({Permission.CREATE} if args.authorize_create else set()) |
        ({Permission.EXTERNAL} if args.authorize_local_inference else set())))
    try:
        image = ComfyUIHost(checkpoint=args.checkpoint, timeout=args.timeout).generate(
            args.prompt, negative_prompt=args.negative_prompt, width=args.width, height=args.height,
            steps=args.steps, seed=args.seed, authorization=auth)
        filename = export_comfy_image(image, args.export_root, args.filename)
        print(json.dumps({"status": "PASSED", "provider": image.provider,
            "model": image.checkpoint, "prompt_id": image.prompt_id,
            "artifact_type": "image/png", "width": image.width, "height": image.height,
            "sha256": image.sha256, "file": filename, "image_verified": True,
            "source_verified": False, "human_reviewed": False}, sort_keys=True))
        return 0
    except IntelError as exc:
        print(json.dumps(exc.as_result()["error"], sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
