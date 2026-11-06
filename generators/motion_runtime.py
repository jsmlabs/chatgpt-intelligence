"""G3.1 offline, bounded procedural motion storyboard and real animated GIF output.

GIF89a frames use a deliberately simple, independently verifiable LZW stream:
each pixel is preceded by a clear code. This trades compression for auditability.
No AI/video model, runtime download, network, scripts or third-party packages.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
from typing import Mapping
from uuid import uuid4

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _require_text
from .theme_runtime import PRESETS, hex_color

MOTIONS = ("pulse", "orbit", "bounce")
FORMATS = ("json", "gif")
MAX_BYTES = 2_000_000
MAX_STORY = 32768
FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:json|gif)\Z")


def motion_capability():
    return replace(default_registry().resolve("GIF"), implemented=True, state=State.AVAILABLE,
                   formats=FORMATS, required_tools=(), risk="low", version="0.1.0",
                   description="Offline procedural motion storyboard and verifiable animated GIF")


def request_motion(argument: str, request: Mapping | None):
    if request is None:
        request = {}
    if not isinstance(request, Mapping) or set(request) - {
        "objective", "motion", "format", "width", "height", "frames",
        "frame_duration_ms", "loop", "preset", "accent",
    }:
        raise IntelError("INVALID_REQUEST", "Unknown or invalid motion request fields")
    objective = _require_text(request.get("objective", argument), "objective",
                              required=True, limit=4096)
    motion = _require_text(request.get("motion", "pulse"), "motion", required=True, limit=16)
    fmt = _require_text(request.get("format", "json"), "format", required=True, limit=16)
    preset = _require_text(request.get("preset", "graphite"), "preset", required=True, limit=32)
    if motion not in MOTIONS or preset not in PRESETS:
        raise IntelError("INVALID_REQUEST", "Unknown motion style or preset")
    if fmt not in FORMATS:
        raise IntelError("UNSUPPORTED_FORMAT", "Motion supports JSON storyboard or GIF")
    accent = hex_color(request["accent"]) if "accent" in request else PRESETS[preset]
    bounds = {"width": (64, 256), "height": (64, 256), "frames": (2, 12),
              "frame_duration_ms": (50, 1000), "loop": (0, 20)}
    values = {}
    defaults = {"width": 128, "height": 128, "frames": 8,
                "frame_duration_ms": 120, "loop": 0}
    for key, (minimum, maximum) in bounds.items():
        val = request.get(key, defaults[key])
        if type(val) is not int or not minimum <= val <= maximum:
            raise IntelError("INVALID_REQUEST", f"{key} must be an integer in {minimum}..{maximum}")
        values[key] = val
    if values["frame_duration_ms"] % 10:
        raise IntelError("INVALID_REQUEST", "GIF frame duration must be a multiple of 10ms")
    return objective, motion, fmt, preset, accent, values


def storyboard(objective: str, motion: str, preset: str, accent: str, values: dict) -> dict:
    frames = values["frames"]
    return {
        "schema_version": "1.0", "capability": "motion",
        "objective": objective, "style": motion, "palette": {
            "background": "#0B1020", "accent": accent,
            "highlight": "#FFFFFF", "surface": "#334155",
        },
        "canvas": {"width": values["width"], "height": values["height"]},
        "timing": {"frames": frames, "frame_duration_ms": values["frame_duration_ms"],
                   "total_duration_ms": frames * values["frame_duration_ms"],
                   "loop": values["loop"], "loop_semantics": "0 is infinite; positive is repeat count"},
        "frames": [{"index": i, "time_ms": i * values["frame_duration_ms"],
                    "phase": round(i / frames, 6),
                    "action": {"pulse": "radial expansion", "orbit": "circular translation",
                               "bounce": "horizontal oscillation"}[motion]}
                   for i in range(frames)],
        "producer": "local-procedural-motion",
        "source_verification": "not_run", "human_review": "not_run",
        "semantic_prompt_followed": False,
        "limitations": "abstract fixed geometry; not arbitrary scene generation or video",
    }


def pixels(width: int, height: int, motion: str, phase: float) -> bytes:
    """Four-entry indexed bitmap; position varies coherently across a loop."""
    out = bytearray(width * height)
    cx = (width - 1) / 2
    cy = (height - 1) / 2
    scale = min(width, height)
    theta = 2 * math.pi * phase
    if motion == "pulse":
        x, y = cx, cy
        radius = scale * (0.13 + 0.10 * (1 - math.cos(theta)) / 2)
    elif motion == "orbit":
        x, y = cx + scale * 0.23 * math.cos(theta), cy + scale * 0.23 * math.sin(theta)
        radius = scale * 0.10
    else:
        x, y = cx + scale * 0.26 * math.sin(theta), cy
        radius = scale * 0.12
    rr = radius * radius
    highlight = (radius * 0.33) ** 2
    for iy in range(height):
        for ix in range(width):
            ds = (ix - x) ** 2 + (iy - y) ** 2
            if ds <= rr:
                out[iy * width + ix] = 2 if (ix - x + radius * 0.28) ** 2 + (iy - y + radius * 0.28) ** 2 < highlight else 1
            elif motion == "orbit":
                ring = (ix - cx) ** 2 + (iy - cy) ** 2
                if (scale * 0.22) ** 2 < ring < (scale * 0.235) ** 2:
                    out[iy * width + ix] = 3
    return bytes(out)


def _lzw_encode(bitmap: bytes) -> bytes:
    """Clear+literal for each pixel; fixed 3-bit codes, valid LZW minimum size 2."""
    accumulator, bits = 0, 0
    packed = bytearray()
    for index in bitmap:
        for code in (4, index):
            accumulator |= code << bits
            bits += 3
            while bits >= 8:
                packed.append(accumulator & 255)
                accumulator >>= 8
                bits -= 8
    accumulator |= 5 << bits
    bits += 3
    while bits >= 8:
        packed.append(accumulator & 255)
        accumulator >>= 8
        bits -= 8
    if bits:
        packed.append(accumulator & 255)
    return bytes(packed)


def _blocks(payload: bytes) -> bytes:
    return b"".join(bytes([len(payload[i:i+255])]) + payload[i:i+255]
                    for i in range(0, len(payload), 255)) + b"\x00"


def render_gif(story: dict) -> bytes:
    width, height = story["canvas"]["width"], story["canvas"]["height"]
    timing = story["timing"]
    colors = [story["palette"][name] for name in ("background", "accent", "highlight", "surface")]
    palette = b"".join(bytes.fromhex(value[1:]) for value in colors)
    result = bytearray(b"GIF89a" + struct.pack("<HHBBB", width, height, 0xF1, 0, 0) + palette)
    result += b"!\xff\x0bNETSCAPE2.0\x03\x01" + struct.pack("<H", timing["loop"]) + b"\x00"
    for item in story["frames"]:
        result += b"!\xf9\x04\x00" + struct.pack("<H", timing["frame_duration_ms"] // 10) + b"\x00\x00"
        result += b"," + struct.pack("<HHHHB", 0, 0, width, height, 0)
        result += b"\x02" + _blocks(_lzw_encode(
            pixels(width, height, story["style"], item["index"] / timing["frames"])))
        if len(result) > MAX_BYTES:
            raise IntelError("OUTPUT_TOO_LARGE", "GIF exceeds 2MB output budget")
    result += b";"
    data = bytes(result)
    verify_gif(data, width=width, height=height, frames=timing["frames"],
               duration_ms=timing["frame_duration_ms"], loop=timing["loop"])
    return data


def _read_subblocks(data: bytes, pos: int):
    chunks = bytearray()
    while True:
        if pos >= len(data):
            raise IntelError("INVALID_GIF", "Truncated GIF subblocks")
        length = data[pos]
        pos += 1
        if length == 0:
            return bytes(chunks), pos
        if pos + length > len(data):
            raise IntelError("INVALID_GIF", "Truncated GIF data block")
        chunks.extend(data[pos:pos+length])
        pos += length


def _verify_simple_lzw(compressed: bytes, pixels_expected: int):
    """Decode this renderer's constrained 3-bit GIF LZW stream and count every pixel."""
    bitbuf, count, bitpos, expecting_clear = 0, 0, 0, True
    total_bits = len(compressed) * 8
    while bitpos + 3 <= total_bits:
        byte_index, bit_shift = divmod(bitpos, 8)
        code = int.from_bytes(compressed[byte_index:byte_index+2], "little") >> bit_shift & 7
        bitpos += 3
        if expecting_clear:
            if code != 4:
                raise IntelError("INVALID_GIF", "Expected clear LZW code")
            expecting_clear = False
        elif code == 5:
            if count != pixels_expected or any((compressed[i // 8] >> (i % 8)) & 1
                                               for i in range(bitpos, total_bits)):
                raise IntelError("INVALID_GIF", "Wrong pixel count or trailing data")
            return
        elif code in (0, 1, 2, 3):
            count += 1
            if count > pixels_expected:
                raise IntelError("INVALID_GIF", "Too many pixels")
            expecting_clear = True
        else:
            raise IntelError("INVALID_GIF", "Invalid LZW literal")
    raise IntelError("INVALID_GIF", "Missing LZW end code")


def verify_gif(data: bytes, *, width: int, height: int, frames: int,
               duration_ms: int, loop: int) -> dict:
    if not isinstance(data, bytes) or not (40 < len(data) <= MAX_BYTES):
        raise IntelError("INVALID_GIF", "GIF bytes missing or too large")
    if data[:6] != b"GIF89a" or len(data) < 25:
        raise IntelError("INVALID_GIF", "Missing GIF89a signature")
    w, h, packed, bg, aspect = struct.unpack("<HHBBB", data[6:13])
    if (w, h, packed, bg, aspect) != (width, height, 0xF1, 0, 0):
        raise IntelError("INVALID_GIF", "Invalid GIF logical screen")
    pos = 25  # header 13 bytes + 4 RGB palette entries
    if data[pos:pos+14] != b"!\xff\x0bNETSCAPE2.0":
        raise IntelError("INVALID_GIF", "Loop extension absent")
    pos += 14
    if data[pos:pos+3] != b"\x03\x01" + struct.pack("<H", loop)[:1]:
        # Loop control is parsed explicitly below instead of assuming byte offsets.
        pass
    if data[pos:pos+5] != b"\x03\x01" + struct.pack("<H", loop) + b"\x00":
        raise IntelError("INVALID_GIF", "Invalid loop extension")
    pos += 5
    for frame in range(frames):
        if data[pos:pos+4] != b"!\xf9\x04\x00":
            raise IntelError("INVALID_GIF", "Missing graphic control extension")
        delay, transparent, terminator = struct.unpack("<HBB", data[pos+4:pos+8])
        if delay != duration_ms // 10 or transparent or terminator:
            raise IntelError("INVALID_GIF", "Invalid frame delay/graphics control")
        pos += 8
        if data[pos:pos+1] != b",":
            raise IntelError("INVALID_GIF", "Missing frame")
        x, y, fw, fh, descriptor = struct.unpack("<HHHHB", data[pos+1:pos+10])
        if (x, y, fw, fh, descriptor) != (0, 0, width, height, 0):
            raise IntelError("INVALID_GIF", "Unexpected frame geometry")
        pos += 10
        if data[pos:pos+1] != b"\x02":
            raise IntelError("INVALID_GIF", "Unsupported GIF LZW code width")
        compressed, pos = _read_subblocks(data, pos + 1)
        _verify_simple_lzw(compressed, width * height)
    if data[pos:] != b";":
        raise IntelError("INVALID_GIF", "Trailing bytes or wrong frame count")
    return {"signature": True, "decoded_frames": frames, "width": width,
            "height": height, "delay_ms": duration_ms, "loop": loop,
            "sha256": hashlib.sha256(data).hexdigest()}


def export_motion(data: bytes | str, root: Path, filename: str, fmt: str):
    if not isinstance(filename, str) or not FILENAME.fullmatch(filename) or not filename.endswith("." + fmt):
        raise IntelError("INVALID_PATH", "Use a plain filename with matching extension")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must exist and not be a symlink")
    payload = data.encode("utf-8") if isinstance(data, str) else data
    base = root.resolve(strict=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        with os.fdopen(os.open(base / filename, flags, 0o600), "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        if (base / filename).read_bytes() != payload:
            raise IntelError("EXPORT_UNVERIFIED", "Export read-back mismatch")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Output already exists") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Motion export failed") from None
    return filename, hashlib.sha256(payload).hexdigest()


class MotionRuntime:
    def __init__(self):
        self.capability = motion_capability()

    def execute(self, raw: str, *, request: Mapping | None = None,
                authorization: Authorization | None = None, export_root: Path | None = None,
                filename: str | None = None, mode: str = "template",
                provider: str | None = None) -> dict:
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "GIF":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE GIF")
            objective, motion, fmt, preset, accent, params = request_motion(command.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if mode != "template" or provider not in (None, "template"):
                raise IntelError("CAPABILITY_UNAVAILABLE", "Motion uses only local procedural rendering")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            manifest = ArtifactManifest(uuid4().hex,
                "image/gif" if fmt == "gif" else "application/json",
                "1.0", (), "motion")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {
                "producer": "local-procedural-motion", "model_provider": "not-used",
                "source_status": "not-checked", "renderer_version": self.capability.version,
            }
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            story = storyboard(objective, motion, preset, accent, params)
            content = (render_gif(story) if fmt == "gif"
                       else json.dumps(story, sort_keys=True, ensure_ascii=True, indent=2) + "\n")
            manifest.transition(ArtifactState.VALIDATING)
            if fmt == "gif":
                check = verify_gif(content, width=params["width"], height=params["height"],
                                   frames=params["frames"], duration_ms=params["frame_duration_ms"],
                                   loop=params["loop"])
                manifest.validations = {"gif_decoded": True, "bounds": len(content) <= MAX_BYTES}
            else:
                parsed = json.loads(content)
                manifest.validations = {"valid_storyboard": parsed == story,
                    "bounded": len(content.encode("utf-8")) <= MAX_STORY,
                    "timing": len(parsed["frames"]) == params["frames"]}
                check = {"storyboard_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "Motion output failed validation")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {
                "structural_validation": "passed", "gif_generated": fmt == "gif",
                "gif_verified": fmt == "gif", "frame_count": params["frames"],
                "frame_duration_ms": params["frame_duration_ms"], "loop": params["loop"],
                "dimensions": [params["width"], params["height"]],
                "source_verification": "not_run", "human_review": "not_run",
                "animation_review": "not_run", "semantic_prompt_followed": False,
                **check,
            }
            if export_root is not None:
                path, sha = export_motion(content, export_root, filename, fmt)
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = sha
            return {"ok": True, "capability": "motion", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in (ArtifactState.FAILED, ArtifactState.EXPORTED):
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
