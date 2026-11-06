"""Dependency-free, deterministic abstract PNG renderer for G2.1.1.

This is procedural geometry, NOT an AI model, prompt-to-image model or photo renderer.
No network, file reads, API key, subprocess or implicit billing. PNG output is checked
before any verified export or MCP image response is reported.
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import zlib

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, safe_relative_path
from .image_runtime import RATIOS
from .text_runtime import _require_text

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 512 * 1024
MAX_PIXELS = 512 * 512
PALETTE = ("#111827", "#6366f1", "#e0e7ff")


def _colors(value: object) -> tuple[tuple[int, int, int], ...]:
    if value is None or value == "":
        value = ",".join(PALETTE)
    if not isinstance(value, str) or len(value) > 128:
        raise IntelError("INVALID_REQUEST", "Palette must be three comma-separated #RRGGBB colors")
    parts = [x.strip() for x in value.split(",")]
    if len(parts) != 3 or any(not re.fullmatch(r"#[0-9a-fA-F]{6}", x) for x in parts):
        raise IntelError("INVALID_REQUEST", "Palette must contain exactly three #RRGGBB colors")
    return tuple(tuple(bytes.fromhex(x[1:])) for x in parts)


def _dimensions(ratio: str) -> tuple[int, int]:
    if ratio not in RATIOS:
        raise IntelError("INVALID_REQUEST", "Unsupported aspect_ratio")
    x, y = (int(v) for v in ratio.split(":"))
    if x >= y:
        width, height = 384, 384 * y // x
    else:
        height, width = 384, 384 * x // y
    if width < 64 or height < 64 or width * height > MAX_PIXELS:
        raise IntelError("INVALID_REQUEST", "Unsupported image dimensions")
    return width, height


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return struct.pack("!I", len(payload)) + tag + payload + struct.pack(
        "!I", zlib.crc32(tag + payload) & 0xFFFFFFFF)


def validate_png(data: object) -> tuple[int, int]:
    """Strict validation of our narrow RGB PNG subset, not arbitrary PNG files."""
    if not isinstance(data, bytes) or not 50 < len(data) <= MAX_PNG_BYTES or not data.startswith(PNG_SIGNATURE):
        raise IntelError("IMAGE_INVALID", "Invalid or oversized PNG")
    offset = len(PNG_SIGNATURE)
    chunks = []
    idat = bytearray()
    while offset + 12 <= len(data):
        size = struct.unpack_from("!I", data, offset)[0]
        if size > MAX_PNG_BYTES or offset + 12 + size > len(data):
            raise IntelError("IMAGE_INVALID", "Malformed PNG chunk length")
        tag = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        actual = struct.unpack_from("!I", data, offset + 8 + size)[0]
        if zlib.crc32(tag + payload) & 0xFFFFFFFF != actual:
            raise IntelError("IMAGE_INVALID", "PNG CRC mismatch")
        chunks.append(tag)
        if tag == b"IDAT":
            idat.extend(payload)
        offset += 12 + size
        if tag == b"IEND":
            break
    if offset != len(data) or chunks != [b"IHDR", b"IDAT", b"IEND"]:
        raise IntelError("IMAGE_INVALID", "Unexpected or missing PNG chunks")
    ihdr = data[len(PNG_SIGNATURE) + 8:len(PNG_SIGNATURE) + 21]
    if len(ihdr) != 13:
        raise IntelError("IMAGE_INVALID", "PNG header truncated")
    w, h, depth, color, compress, filt, interlace = struct.unpack("!IIBBBBB", ihdr)
    if not (64 <= w <= 512 and 64 <= h <= 512 and w * h <= MAX_PIXELS and
            (depth, color, compress, filt, interlace) == (8, 2, 0, 0, 0)):
        raise IntelError("IMAGE_INVALID", "Unsupported PNG header")
    expected = h * (1 + 3 * w)
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(bytes(idat), expected + 1)
    except zlib.error:
        raise IntelError("IMAGE_INVALID", "Invalid PNG compressed data") from None
    # Do not flush untrusted streams: that operation has no output size bound.
    if (len(raw) != expected or not decompressor.eof or
            decompressor.unused_data or decompressor.unconsumed_tail):
        raise IntelError("IMAGE_INVALID", "Incorrect PNG pixel data length")
    row_bytes = 1 + 3 * w
    if any(raw[pos] != 0 for pos in range(0, len(raw), row_bytes)):
        raise IntelError("IMAGE_INVALID", "Unsupported PNG scanline filter")
    return w, h


def render_abstract_png(objective: str, aspect_ratio: str = "1:1",
                        palette: str = "") -> bytes:
    """Generate reproducible decorative raster artwork from an objective seed.

    The objective affects arrangement only; this renderer cannot depict semantic
    subjects, draw labels, honor detailed style prompts or verify image rights.
    """
    objective = _require_text(objective, "objective", required=True)
    w, h = _dimensions(aspect_ratio)
    bg, accent, light = _colors(palette)
    seed = hashlib.sha256(objective.encode("utf-8")).digest()
    phase = seed[0] / 255.0
    scale = 0.20 + seed[1] / 255.0 * 0.24
    center = 0.28 + seed[2] / 255.0 * 0.42
    rows = bytearray()
    for y in range(h):
        rows.append(0)
        v = y / max(1, h - 1)
        for x in range(w):
            u = x / max(1, w - 1)
            gradient = 0.10 + 0.23 * (1.0 - v)
            dx, dy = u - center, v - (0.44 + phase * 0.12)
            ring = abs((dx * dx + dy * dy) ** 0.5 - scale) < 0.035
            sweep = abs((u * 0.75 + v * 0.95 + phase * 0.5) % 1.0 - 0.5) < 0.045
            glow = max(0.0, 1.0 - (dx * dx + dy * dy) / 0.20)
            weight = min(0.84, gradient + glow * 0.35 + (0.38 if sweep else 0))
            if ring:
                color = light
            else:
                color = tuple(min(255, int(bg[i] * (1 - weight) + accent[i] * weight)) for i in range(3))
            rows.extend(color)
    png = (PNG_SIGNATURE +
           _chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
           _chunk(b"IDAT", zlib.compress(bytes(rows), 8)) +
           _chunk(b"IEND", b""))
    validate_png(png)
    return png


@dataclass(frozen=True)
class RenderedImage:
    png: bytes
    width: int
    height: int
    sha256: str
    producer: str = "local-procedural-geometry"
    model_provider: str = "not-used"
    mime_type: str = "image/png"


def render_image(objective: str, *, aspect_ratio: str = "1:1",
                 palette: str = "", authorization: Authorization | None = None) -> RenderedImage:
    (authorization or Authorization()).require(frozenset({Permission.CREATE}))
    data = render_abstract_png(objective, aspect_ratio, palette)
    w, h = validate_png(data)
    return RenderedImage(data, w, h, hashlib.sha256(data).hexdigest())


def export_png(image: RenderedImage, root: Path, name: str) -> tuple[str, str]:
    relative = safe_relative_path(name)
    if not relative.endswith(".png") or "/" in relative:
        raise IntelError("INVALID_PATH", "Export requires a plain .png filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must be an existing non-symlink directory")
    if hashlib.sha256(image.png).hexdigest() != image.sha256:
        raise IntelError("IMAGE_INVALID", "Image checksum mismatch")
    validate_png(image.png)
    target = root / relative
    if target.is_symlink():
        raise IntelError("INVALID_PATH", "Export target must not be a symlink")
    try:
        with target.open("xb") as handle:
            handle.write(image.png)
            handle.flush()
            os.fsync(handle.fileno())
        readback = target.read_bytes()
        if readback != image.png or validate_png(readback) != (image.width, image.height):
            raise IntelError("EXPORT_UNVERIFIED", "PNG readback differs from source")
        return relative, image.sha256
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite existing PNG") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Could not safely export PNG") from None
    except IntelError:
        try:
            target.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an offline abstract PNG (not AI-generated)")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--aspect-ratio", default="1:1", choices=sorted(RATIOS))
    parser.add_argument("--palette", default="")
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--authorize-create", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = render_image(args.objective, aspect_ratio=args.aspect_ratio,
                              palette=args.palette, authorization=Authorization(
                                  frozenset({Permission.CREATE}) if args.authorize_create else frozenset()))
        path, digest = export_png(result, args.export_root, args.filename)
        print(json.dumps({"state": "exported", "artifact_type": "image/png", "filename": path,
                          "sha256": digest, "width": result.width, "height": result.height,
                          "image_generated": True, "image_verified": True,
                          "producer": result.producer, "model_provider": "not-used",
                          "semantic_prompt_followed": False}, sort_keys=True))
        return 0
    except IntelError as exc:
        print(json.dumps(exc.as_result()["error"], sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
