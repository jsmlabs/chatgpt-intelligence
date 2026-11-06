"""G2.3 deterministic color themes, DTCG-style tokens, CSS and WCAG 2.2 pair checks.

No models, network, filesystem writes through MCP or accessibility certification.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _require_text

HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")
FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:json|css)\Z")
PRESETS = {
    "graphite": "#5266EA",
    "ocean": "#006FC9",
    "plum": "#9148C8",
    "forest": "#237753",
}
ROLES = ("background", "surface", "text", "muted_text", "accent", "on_accent",
         "border", "focus", "success", "on_success", "danger", "on_danger")
SIZE_LIMIT = 32768


def theme_capability():
    return replace(default_registry().resolve("THEME"), state=State.AVAILABLE,
                   implemented=True, formats=("json", "css"), required_tools=(),
                   risk="low", version="0.1.0",
                   description="Offline light/dark color tokens with WCAG contrast audit")


def hex_color(value: str) -> str:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise IntelError("INVALID_REQUEST", "Color must be #RRGGBB")
    return value.upper()


def relative_luminance(value: str) -> float:
    channels = [int(hex_color(value)[i:i+2], 16) / 255.0 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
              for v in channels]
    return sum(a * b for a, b in zip((0.2126, 0.7152, 0.0722), linear))


def contrast_ratio(first: str, second: str) -> float:
    x, y = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def readable_ink(background: str) -> str:
    return "#000000" if contrast_ratio("#000000", background) >= contrast_ratio("#FFFFFF", background) else "#FFFFFF"


def palette_for(accent: str) -> dict[str, dict[str, str]]:
    """Semantic surfaces are fixed for predictable contrast; accent is configurable."""
    return {
        "light": {
            "background": "#FFFFFF", "surface": "#F1F5F9", "text": "#111827",
            "muted_text": "#334155", "accent": accent,
            "on_accent": readable_ink(accent), "border": "#64748B",
            "focus": "#1D4ED8", "success": "#146C43",
            "on_success": readable_ink("#146C43"), "danger": "#B91C1C",
            "on_danger": readable_ink("#B91C1C"),
        },
        "dark": {
            "background": "#0B1020", "surface": "#1F2937", "text": "#F8FAFC",
            "muted_text": "#CBD5E1", "accent": accent,
            "on_accent": readable_ink(accent), "border": "#94A3B8",
            "focus": "#93C5FD", "success": "#34D399",
            "on_success": readable_ink("#34D399"), "danger": "#FCA5A5",
            "on_danger": readable_ink("#FCA5A5"),
        },
    }


PAIR_RULES = (
    ("text", "background", "normal_text_aa", 4.5),
    ("text", "surface", "normal_text_aa", 4.5),
    ("muted_text", "background", "normal_text_aa", 4.5),
    ("muted_text", "surface", "normal_text_aa", 4.5),
    ("on_accent", "accent", "normal_text_aa", 4.5),
    ("on_success", "success", "normal_text_aa", 4.5),
    ("on_danger", "danger", "normal_text_aa", 4.5),
    ("border", "background", "non_text_aa", 3.0),
    ("border", "surface", "non_text_aa", 3.0),
    ("focus", "background", "non_text_aa", 3.0),
    ("focus", "surface", "non_text_aa", 3.0),
)


def audit(palettes: Mapping[str, Mapping[str, str]]) -> dict:
    results = []
    for mode in ("light", "dark"):
        colors = palettes[mode]
        for foreground, background, criterion, minimum in PAIR_RULES:
            value = contrast_ratio(colors[foreground], colors[background])
            results.append({
                "mode": mode, "foreground": foreground, "background": background,
                "ratio": round(value, 4), "minimum": minimum, "criterion": criterion,
                "passed": value >= minimum,
            })
        # AAA is recorded separately; AAA failure does not fail the AA contract.
        value = contrast_ratio(colors["text"], colors["background"])
        results.append({"mode": mode, "foreground": "text", "background": "background",
                        "ratio": round(value, 4), "minimum": 7.0,
                        "criterion": "normal_text_aaa", "passed": value >= 7.0})
    aa = [r for r in results if r["criterion"] != "normal_text_aaa"]
    return {"wcag_version": "2.2", "method": "sRGB relative luminance",
            "pair_results": results, "aa_passed": all(r["passed"] for r in aa),
            "aaa_text_background_passed": all(r["passed"] for r in results
                                               if r["criterion"] == "normal_text_aaa"),
            "scope": "only enumerated opaque hex color pairs; no full UI assessment"}


def validate_theme_request(argument: str, request: Mapping[str, object] | None):
    if request is None:
        request = {}
    if not isinstance(request, Mapping) or set(request) - {"objective", "preset", "accent", "format"}:
        raise IntelError("INVALID_REQUEST", "Unknown THEME request field")
    objective = _require_text(request.get("objective", argument), "objective", required=True, limit=8192)
    preset = _require_text(request.get("preset", "graphite"), "preset", required=True, limit=32)
    fmt = _require_text(request.get("format", "json"), "format", required=True, limit=16)
    if preset not in PRESETS:
        raise IntelError("INVALID_REQUEST", "Unsupported theme preset")
    if fmt not in ("json", "css"):
        raise IntelError("UNSUPPORTED_FORMAT", "THEME supports json or css")
    accent = hex_color(request["accent"]) if "accent" in request else PRESETS[preset]
    return objective, preset, fmt, accent


def build_tokens(objective: str, preset: str, accent: str) -> dict:
    palettes = palette_for(accent)
    result = audit(palettes)
    if not result["aa_passed"]:
        raise IntelError("CONTRAST_FAILED", "Preset failed audited WCAG AA color pairs")
    return {
        "schema_version": "1.0",
        "capability": "theme",
        "objective": objective,
        "preset": preset,
        "tokens": {
            mode: {
                "color": {role: {"$type": "color", "$value": palette[role]} for role in ROLES},
                "font": {"family": {"$type": "fontFamily", "$value": ["system-ui", "sans-serif"]}},
                "spacing": {name: {"$type": "dimension", "$value": f"{n}px"}
                            for name, n in (("xs", 4), ("sm", 8), ("md", 16), ("lg", 24), ("xl", 32))},
                "radius": {"md": {"$type": "dimension", "$value": "8px"}},
            }
            for mode, palette in palettes.items()
        },
        "contrast_audit": result,
        "provenance": {"producer": "local-deterministic-template",
                       "model_provider": "not-used", "browser_test": "not_run",
                       "accessibility_certification": "not_run",
                       "source_verification": "not_run"},
    }


def render_css(tokens: Mapping) -> str:
    def variables(mode: str) -> str:
        t = tokens["tokens"][mode]
        lines = [f"  --intel-{role.replace('_', '-')}: {value['$value']};"
                 for role, value in t["color"].items()]
        lines += [f"  --intel-space-{name}: {entry['$value']};"
                  for name, entry in t["spacing"].items()]
        lines.append("  --intel-radius-md: 8px;")
        lines.append("  --intel-font-family: system-ui, sans-serif;")
        return "\n".join(lines)
    return ("/* INTEL THEME v0.1.0; static tokens, not WCAG site certification. */\n"
            ":root, [data-theme=\"light\"] {\n" + variables("light") + "\n}\n"
            "@media (prefers-color-scheme: dark) {\n"
            "  :root:not([data-theme=\"light\"]) {\n" + variables("dark") + "\n  }\n}\n"
            "[data-theme=\"dark\"] {\n" + variables("dark") + "\n}\n")


def serialize(tokens: dict, fmt: str) -> str:
    result = (json.dumps(tokens, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
              if fmt == "json" else render_css(tokens))
    if len(result.encode("utf-8")) > SIZE_LIMIT:
        raise IntelError("VALIDATION_FAILED", "THEME artifact exceeds size budget")
    return result


def validate_output(content: str, fmt: str) -> dict[str, bool]:
    try:
        size = len(content.encode("utf-8"))
    except UnicodeError:
        size = 0
    checks = {"bounded": 0 < size <= SIZE_LIMIT, "no_nul": "\x00" not in content}
    if fmt == "json":
        try:
            value = json.loads(content)
            checks["json_structure"] = (isinstance(value, dict)
                and value.get("contrast_audit", {}).get("aa_passed") is True
                and set(value.get("tokens", {})) == {"light", "dark"})
        except (ValueError, TypeError, AttributeError):
            checks["json_structure"] = False
    else:
        checks["css_tokens"] = (":root, [data-theme=\"light\"]" in content
                                and "[data-theme=\"dark\"]" in content
                                and "--intel-on-accent:" in content)
        checks["no_remote_import"] = not re.search(r"@import|url\s*\(", content, re.I)
    return checks


def export_theme(content: str, root: Path, filename: str, fmt: str) -> tuple[str, str]:
    if not isinstance(filename, str) or not FILENAME.fullmatch(filename) or not filename.endswith("." + fmt):
        raise IntelError("INVALID_PATH", "Use a plain matching .json or .css filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Export root must be an existing non-symlink directory")
    if not all(validate_output(content, fmt).values()):
        raise IntelError("VALIDATION_FAILED", "Invalid theme output")
    payload = content.encode("utf-8")
    base = root.resolve(strict=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(base / filename, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if (base / filename).read_bytes() != payload:
            raise IntelError("EXPORT_UNVERIFIED", "THEME output readback differs")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite existing theme") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "THEME export failed") from None
    return filename, hashlib.sha256(payload).hexdigest()


class ThemeRuntime:
    def __init__(self):
        self.capability = theme_capability()

    def execute(self, raw: str, *, request: Mapping[str, object] | None = None,
                authorization: Authorization | None = None,
                export_root: Path | None = None, filename: str | None = None,
                provider: str | None = None, mode: str = "template") -> dict:
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "THEME":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE THEME")
            objective, preset, fmt, accent = validate_theme_request(command.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if mode != "template" or provider not in (None, "template"):
                raise IntelError("CAPABILITY_UNAVAILABLE", "No connected theme model provider")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            manifest = ArtifactManifest(uuid4().hex, "application/json" if fmt == "json"
                                        else "text/css", "1.0", (), "theme")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {"producer": "local-deterministic-template",
                                   "model_provider": "not-used", "source_status": "unverified",
                                   "renderer_version": self.capability.version}
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            tokens = build_tokens(objective, preset, accent)
            content = serialize(tokens, fmt)
            manifest.transition(ArtifactState.VALIDATING)
            manifest.validations = validate_output(content, fmt)
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "THEME output failed validation")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {"structural_validation": "passed",
                        "contrast_audit": tokens["contrast_audit"],
                        "browser_test": "not_run",
                        "accessibility_certification": "not_run",
                        "source_verification": "not_run", "human_review": "not_run"}
            if export_root is not None:
                path, digest = export_theme(content, export_root, filename, fmt)
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "theme", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in {ArtifactState.FAILED, ArtifactState.EXPORTED}:
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
