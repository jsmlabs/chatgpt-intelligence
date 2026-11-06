"""G2.4 deterministic BRAND identity briefs, theme-compatible tokens and vector concepts.

An SVG here is an original geometric logo *concept*, not a legally cleared
trademark, unique identity, or raster/AI generated image. No network/providers.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from html import escape as xml_escape
import json
import os
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4
from xml.etree import ElementTree

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _require_text, _items, _inline, _check_markdown, export_markdown
from .theme_runtime import PRESETS, hex_color, build_tokens, contrast_ratio

DIRECTIONS = {
    "orbit": "A concentric orbital geometry conveying connectivity and continuity.",
    "signal": "A geometric pulse line communicating observation and momentum.",
    "aperture": "A modular aperture mark suggesting focus and craft.",
}
FORMATS = ("markdown", "json", "svg")
MAX_ARTIFACT = 65536
FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:json|svg)\Z")


def brand_capability():
    return replace(default_registry().resolve("BRAND"), state=State.AVAILABLE,
                   implemented=True, formats=FORMATS, required_tools=(), risk="low",
                   version="0.1.0", description="Deterministic brand brief, tokens and SVG logo concept")


def validate_brand_request(argument: str, request: Mapping[str, object] | None):
    if request is None:
        request = {}
    if not isinstance(request, Mapping) or set(request) - {
        "objective", "name", "audience", "values", "style", "preset", "accent",
        "direction", "format",
    }:
        raise IntelError("INVALID_REQUEST", "Unknown BRAND fields")
    objective = _require_text(request.get("objective", argument), "objective", required=True, limit=8192)
    name = _require_text(request.get("name", ""), "name", required=True, limit=96)
    audience = _require_text(request.get("audience", "General audience"), "audience",
                             required=True, limit=512)
    style = _require_text(request.get("style", "Minimal geometric"), "style", required=True, limit=512)
    values = _items(request.get("values", []), "values")
    if len(values) > 8:
        raise IntelError("INVALID_REQUEST", "At most eight brand values")
    preset = _require_text(request.get("preset", "graphite"), "preset", required=True, limit=32)
    direction = _require_text(request.get("direction", "orbit"), "direction", required=True, limit=32)
    fmt = _require_text(request.get("format", "markdown"), "format", required=True, limit=16)
    if preset not in PRESETS or direction not in DIRECTIONS:
        raise IntelError("INVALID_REQUEST", "Unknown preset or logo direction")
    if fmt not in FORMATS:
        raise IntelError("UNSUPPORTED_FORMAT", "BRAND supports markdown, json and svg")
    accent = hex_color(request["accent"]) if "accent" in request else PRESETS[preset]
    # Schematic mark labels are small; reject invisible/no-print characters.
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise IntelError("INVALID_REQUEST", "Brand name contains control characters")
    return objective, name, audience, style, values, preset, accent, direction, fmt


def identity_payload(objective, name, audience, style, values, preset, accent, direction):
    tokens = build_tokens(objective, preset, accent)
    return {
        "schema_version": "1.0",
        "capability": "brand",
        "name": name,
        "objective": objective,
        "audience": audience,
        "style": style,
        "values": list(values),
        "selected_logo_direction": direction,
        "logo_directions": [{"id": key, "description": description}
                            for key, description in DIRECTIONS.items()],
        "asset_contract": {
            "mark": "512x512 SVG geometric concept, not registered or rights-cleared",
            "clear_space": "At least one eighth of mark width",
            "minimum_size": "Review legibility manually at 24px and 48px",
            "variants": ["light", "dark", "single-color"],
            "do_not": ["stretch", "recolor outside token palette", "imply trademark clearance"],
        },
        "theme": tokens,
        "provenance": {
            "producer": "local-deterministic-template",
            "model_provider": "not-used",
            "sources": "none-verified",
            "trademark_review": "not_run",
            "human_review": "not_run",
            "browser_render": "not_run",
        },
    }


def brand_brief(value: dict) -> str:
    lines = [
        "# Brand Identity Brief", "",
        "## Positioning", "",
        "- Brand name: " + _inline(value["name"]),
        "- Objective: " + _inline(value["objective"]),
        "- Audience: " + _inline(value["audience"]),
        "- Creative style: " + _inline(value["style"]), "",
        "## Brand values", "",
    ]
    lines += ["- " + _inline(v) for v in value["values"]] or ["- Not specified"]
    lines += ["", "## Logo directions", ""]
    for direction in value["logo_directions"]:
        lines.append("- **" + direction["id"] + "**: " + direction["description"])
    lines += ["", "## Selected direction", "",
              "- " + value["selected_logo_direction"], "",
              "## Reusable design system", "",
              "- Tokens: G2.3 light/dark color, spacing, typography and radius.",
              "- Primary accent: " + value["theme"]["tokens"]["light"]["color"]["accent"]["$value"],
              "- Color-pair audit: " + ("passed" if value["theme"]["contrast_audit"]["aa_passed"] else "failed"),
              "- Define wordmark typography after reviewing real usage.", "",
              "## Asset usage rules", ""]
    lines += ["- " + x for x in value["asset_contract"]["do_not"]]
    lines += ["- Minimum size: " + value["asset_contract"]["minimum_size"],
              "- Clear space: " + value["asset_contract"]["clear_space"], "",
              "## Review and acceptance", "",
              "- Check distinctiveness against real-world marks and relevant trademarks.",
              "- Review copyright, licensing and brand name before any publication.",
              "- Inspect mark at small sizes and on light/dark backgrounds.",
              "- Test final typography, legibility, contrast, export and reproduction.", "",
              "## Provenance and limitations", "",
              "Local deterministic draft. SVG is a geometric *concept* only, not a "
              "certified original or exclusive trademark. No rights, browser, "
              "human design or legal review has occurred.", ""]
    return "\n".join(lines)


def logo_svg(value: dict) -> str:
    """No arbitrary SVG injection: fixed path geometry, escaped title, validated colors."""
    name = xml_escape(value["name"], quote=True)
    accent = value["theme"]["tokens"]["dark"]["color"]["accent"]["$value"]
    background = value["theme"]["tokens"]["dark"]["color"]["background"]["$value"]
    ink = value["theme"]["tokens"]["dark"]["color"]["on_accent"]["$value"]
    direction = value["selected_logo_direction"]
    if direction == "orbit":
        shape = ('<circle cx="256" cy="256" r="124" fill="none" stroke="{a}" stroke-width="34"/>'
                 '<circle cx="256" cy="256" r="53" fill="{a}"/>'
                 '<circle cx="363" cy="169" r="27" fill="{a}"/>').format(a=accent)
    elif direction == "signal":
        shape = ('<path d="M106 271 H180 L223 170 L283 343 L323 248 H406" '
                 'fill="none" stroke="{a}" stroke-width="34" stroke-linecap="round" '
                 'stroke-linejoin="round"/>').format(a=accent)
    else:
        shape = ('<path d="M256 109 L373 171 L373 302 L256 385 L139 302 L139 171 Z" '
                 'fill="none" stroke="{a}" stroke-width="30"/>'
                 '<circle cx="256" cy="248" r="65" fill="{a}"/>').format(a=accent)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" '
        'aria-labelledby="brand-title brand-desc">'
        '<title id="brand-title">' + name + ' - ' + direction + ' logo concept</title>'
        '<desc id="brand-desc">Unreviewed geometric mark concept. Not trademark cleared.</desc>'
        '<rect width="512" height="512" rx="90" fill="' + background + '"/>'
        + shape + '</svg>\n'
    )


def validate_svg(svg: str) -> dict[str, bool]:
    checks = {
        "bounded": isinstance(svg, str) and 0 < len(svg.encode("utf-8")) <= MAX_ARTIFACT,
        "no_script": not re.search(r"<script\b|<foreignObject\b|\son[a-z]+\s*=", svg, re.I),
        "no_external": not re.search(r"\b(?:href|src)\s*=|url\s*\(|<!DOCTYPE|<!ENTITY", svg, re.I),
        "has_title": "<title " in svg and "<desc " in svg,
    }
    try:
        root = ElementTree.fromstring(svg)
        checks["valid_svg"] = root.tag == "{http://www.w3.org/2000/svg}svg"
        safe = {"svg", "title", "desc", "rect", "circle", "path"}
        checks["allowed_elements"] = all(
            item.tag.removeprefix("{http://www.w3.org/2000/svg}") in safe
            for item in root.iter()
        )
    except (ElementTree.ParseError, ValueError):
        checks["valid_svg"] = checks["allowed_elements"] = False
    return checks


def validate_content(content: str, fmt: str, data: dict) -> dict[str, bool]:
    if fmt == "markdown":
        return _check_markdown(content)
    if fmt == "svg":
        return validate_svg(content)
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        return {"valid_json": False}
    return {
        "bounded": 0 < len(content.encode("utf-8")) <= MAX_ARTIFACT,
        "valid_json": parsed == data,
        "theme_audited": parsed.get("theme", {}).get("contrast_audit", {}).get("aa_passed") is True,
    }


def export_brand(content: str, root: Path, filename: str, fmt: str):
    """Exclusive single-file export, matching format and readback checksum."""
    if fmt == "markdown":
        return export_markdown(content, root, filename)
    if not isinstance(filename, str) or not FILENAME.fullmatch(filename) or not filename.endswith("." + fmt):
        raise IntelError("INVALID_PATH", "Output must be a plain matching .json or .svg filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must be an existing non-symlink directory")
    payload = content.encode("utf-8")
    directory = root.resolve(strict=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(directory / filename, flags, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        if (directory / filename).read_bytes() != payload:
            raise IntelError("EXPORT_UNVERIFIED", "Export readback mismatch")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite brand asset") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "Brand export failed") from None
    return filename, hashlib.sha256(payload).hexdigest()


class BrandRuntime:
    def __init__(self):
        self.capability = brand_capability()

    def execute(self, raw: str, *, request: Mapping[str, object] | None = None,
                authorization: Authorization | None = None,
                export_root: Path | None = None, filename: str | None = None,
                provider: str | None = None, mode: str = "template") -> dict:
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "BRAND":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE BRAND")
            fields = validate_brand_request(command.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if provider not in (None, "template") or mode != "template":
                raise IntelError("CAPABILITY_UNAVAILABLE", "No model-backed brand provider is connected")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            fmt = fields[-1]
            value = identity_payload(*fields[:-1])
            if fmt == "markdown":
                content = brand_brief(value)
            elif fmt == "json":
                content = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
            else:
                content = logo_svg(value)
            manifest = ArtifactManifest(uuid4().hex, {
                "markdown": "text/markdown", "json": "application/json", "svg": "image/svg+xml"
            }[fmt], "1.0", (), "brand")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {
                "producer": "local-deterministic-template",
                "model_provider": "not-used", "source_status": "unverified",
                "renderer_version": self.capability.version,
            }
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            manifest.transition(ArtifactState.VALIDATING)
            manifest.validations = validate_content(content, fmt, value)
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "BRAND artifact failed checks")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {
                "structural_validation": "passed",
                "contrast_audit": value["theme"]["contrast_audit"],
                "logo_direction": value["selected_logo_direction"],
                "trademark_review": "not_run", "human_review": "not_run",
                "browser_render": "not_run", "source_verification": "not_run",
                "model_generation": "not_run",
            }
            if export_root is not None:
                path, digest = export_brand(content, export_root, filename, fmt)
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "brand", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in (ArtifactState.FAILED, ArtifactState.EXPORTED):
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
