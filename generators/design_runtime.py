"""Deterministic DESIGN specifications and inert responsive HTML previews."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone
from html import escape
import hashlib
import os
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import _check_markdown, _inline, _items, _require_text, export_markdown, validate_request

LAYOUTS = {"dashboard", "landing", "form", "catalog"}
RESPONSIVE = {"mobile-first", "desktop-first"}
COMPONENTS = {"header", "navigation", "hero", "summary", "cards", "filters", "form", "footer"}
DEFAULTS = {
    "dashboard": ("header", "navigation", "summary", "cards", "filters", "footer"),
    "landing": ("header", "navigation", "hero", "cards", "footer"),
    "form": ("header", "navigation", "form", "footer"),
    "catalog": ("header", "navigation", "filters", "cards", "footer"),
}


def design_capability():
    return replace(default_registry().resolve("DESIGN"), state=State.AVAILABLE,
                   implemented=True, formats=("markdown", "html"), risk="low",
                   version="0.1.0", description="Local design specification and static HTML preview")


def validate_design_request(argument, values):
    if not isinstance(values, Mapping):
        raise IntelError("INVALID_REQUEST", "Design request must be an object")
    layout = _require_text(values.get("layout", "dashboard"), "layout", required=True, limit=32)
    responsive = _require_text(values.get("responsive", "mobile-first"),
                               "responsive", required=True, limit=32)
    if layout not in LAYOUTS or responsive not in RESPONSIVE:
        raise IntelError("INVALID_REQUEST", "Unsupported layout or responsive strategy")
    requested = values.get("components")
    components = DEFAULTS[layout] if requested is None else _items(requested, "components")
    if not components or len(components) != len(set(components)) or any(x not in COMPONENTS for x in components):
        raise IntelError("INVALID_REQUEST", "Unsupported or duplicate component")
    shared = {k: v for k, v in values.items() if k not in {"layout", "responsive", "components"}}
    brief = validate_request(argument, {**shared, "format": "markdown"})
    return brief, layout, responsive, components


def render_design_spec(brief, layout, responsive, components):
    lines = [
        "# Design Specification", "", "## Product brief", "",
        "- Objective: " + _inline(brief.objective),
        "- Audience: " + _inline(brief.audience),
        "- Style: " + _inline(brief.style or "Not supplied"),
        "- Layout: " + layout, "- Responsive: " + responsive, "",
        "## Information architecture", "",
        "- Prioritize purpose, task navigation and readable supporting content.",
        "- Define loading, empty, success and error states before app development.", "",
        "## Component inventory", "",
    ]
    lines.extend("- " + x + ": semantic role, state and responsive behavior to validate." for x in components)
    lines.extend(["", "## Responsive specification", "",
        "- 320-639px: single column, natural scrolling.",
        "- 640-959px: two columns where relevant.",
        "- 960px+: bounded content width, three columns where relevant.",
        "- Inspect at 320, 375, 768, 1024 and 1440px in a real browser.", "",
        "## Accessibility acceptance", "",
        "- Preserve landmarks, heading order, labels and keyboard focus.",
        "- Test actual contrast values, screen reader reading order and touch targets.",
        "- Respect reduced motion and avoid interaction-only information.", "",
        "## Constraints", ""])
    lines.extend("- " + _inline(x) for x in brief.constraints)
    if not brief.constraints: lines.append("- None supplied")
    lines.extend(["", "## Unverified sources", ""])
    lines.extend("- " + _inline(x) for x in brief.sources)
    if not brief.sources: lines.append("- None supplied")
    lines.extend(["", "## Verification plan", ""])
    lines.extend("- " + _inline(x) for x in brief.verification)
    lines.extend(["- Verify cross-device layout and behavior in a browser.",
                  "- Perform human accessibility and visual reviews.", "",
                  "## Provenance and limitations", "",
                  "Deterministic local specification, not a tested or interactive application. "
                  "No model call, browser validation, external research or human review.", ""])
    return "\n".join(lines)


def render_html(brief, layout, responsive, components):
    title, audience, style = (escape(brief.objective), escape(brief.audience),
                              escape(brief.style or "Not specified"))
    sections = []
    for component in components:
        if component == "header":
            sections.append('<header class="bar"><strong>INTEL / DESIGN</strong><span>Static prototype</span></header>')
        elif component == "navigation":
            sections.append('<nav aria-label="Navigation preview">Overview | Details | Review</nav>')
        elif component == "hero":
            sections.append('<section><h2>Overview</h2><p>' + title + '</p></section>')
        elif component == "summary":
            sections.append('<section><h2>Summary</h2><p>For ' + audience + '</p></section>')
        elif component == "cards":
            sections.append('<section><h2>Content blocks</h2><div class="cards">'
                            + ''.join('<article><h3>' + x + '</h3><p>Content placeholder</p></article>'
                                      for x in ("Primary", "Secondary", "Review")) + '</div></section>')
        elif component == "filters":
            sections.append('<section><h2>Filter placement</h2><p>Non-interactive preview.</p></section>')
        elif component == "form":
            sections.append('<section><h2>Form placement</h2><p>Field and validation states '
                            'require implementation.</p></section>')
        elif component == "footer":
            sections.append('<footer>Structure-only preview - not a production application</footer>')
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>INTEL DESIGN</title><style>'
            ':root{font:16px/1.5 system-ui;color-scheme:light dark}'
            '*{box-sizing:border-box}body{margin:0;background:#f8fafc;color:#172033}'
            '.wrap{max-width:72rem;margin:auto;padding:1rem}'
            '.bar,nav,footer{padding:1rem;border-bottom:1px solid #64748b}'
            '.bar{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}'
            'main{display:grid;gap:1rem}section,article{padding:1rem;border:1px solid #64748b;'
            'border-radius:.75rem;background:#fff}h1,h2,h3,p{overflow-wrap:anywhere}'
            '.cards{display:grid;gap:1rem;grid-template-columns:1fr}'
            '@media(min-width:640px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}'
            '@media(min-width:960px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}'
            '@media(prefers-color-scheme:dark){body{background:#111827;color:#f1f5f9}'
            'section,article{background:#1f2937}}'
            '@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;'
            'transition:none!important}}</style></head><body><div class="wrap">'
            '<a href="#main">Skip to content</a><h1>' + title + '</h1><p>Audience: ' + audience +
            ' | Style: ' + style + ' | Layout: ' + layout + ' | Strategy: ' + responsive +
            '</p><main id="main">' + '\n'.join(sections) + '</main>'
            '<p>Static HTML only. No working controls, real data or browser verification.</p>'
            '</div></body></html>\n')
    if len(html.encode("utf-8")) > 65536:
        raise IntelError("VALIDATION_FAILED", "HTML budget exceeded")
    return html


def validate_html(content):
    return {
        "bounded": len(content.encode("utf-8")) <= 65536,
        "document": content.startswith("<!doctype html>") and content.endswith("</html>\n"),
        "no_scripts": not re.search(r"<script\b|<[^>]+\bon\w+\s*=", content, re.I),
        "no_remote_assets": not re.search(r'\b(?:src|href)\s*=\s*["\x27](?:https?:|//|data:)', content, re.I),
        "responsive": "@media(min-width:640px)" in content and "@media(min-width:960px)" in content,
        "landmarks": '<main id="main">' in content and "<h1>" in content,
    }


def export_html(content: str, root: Path, filename: str):
    if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.html", filename):
        raise IntelError("INVALID_PATH", "Use a plain .html filename")
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        raise IntelError("INVALID_PATH", "Output root must be an existing non-symlink directory")
    if not all(validate_html(content).values()):
        raise IntelError("VALIDATION_FAILED", "Unsafe or invalid HTML")
    directory = root.resolve(strict=True)
    payload = content.encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(directory / filename, flags, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if (directory / filename).read_bytes() != payload:
            raise IntelError("EXPORT_UNVERIFIED", "Export differs from source")
    except FileExistsError:
        raise IntelError("DESTINATION_EXISTS", "Refusing to overwrite artifact") from None
    except OSError:
        raise IntelError("EXPORT_FAILED", "HTML export failed") from None
    return filename, hashlib.sha256(payload).hexdigest()


class DesignRuntime:
    def __init__(self):
        self.capability = design_capability()

    def execute(self, raw, *, request=None, authorization=None, export_root=None,
                filename=None, provider=None, mode="template"):
        manifest = None
        try:
            command = parse_command(raw)
            if command.name != "GENERATE" or command.generator != "DESIGN":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE DESIGN")
            if not isinstance(request, Mapping) and request is not None:
                raise IntelError("INVALID_REQUEST", "Design request must be an object")
            values = dict(request or {})
            fmt = _require_text(values.get("format", "markdown"), "format", required=True, limit=32)
            if fmt not in ("markdown", "html"):
                raise IntelError("UNSUPPORTED_FORMAT", "Only markdown and static html supported")
            brief, layout, responsive, components = validate_design_request(command.argument, values)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if mode != "template" or provider not in (None, "template"):
                raise IntelError("CAPABILITY_UNAVAILABLE", "No connected design model")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename")
            manifest = ArtifactManifest(uuid4().hex, "text/html" if fmt == "html" else "text/markdown",
                                        "1.0", brief.sources, "design")
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {"producer": "local-deterministic-template",
                                   "model_provider": "not-used", "source_status": "unverified",
                                   "renderer_version": self.capability.version}
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            content = (render_html(brief, layout, responsive, components) if fmt == "html"
                       else render_design_spec(brief, layout, responsive, components))
            manifest.transition(ArtifactState.VALIDATING)
            manifest.validations = validate_html(content) if fmt == "html" else _check_markdown(content)
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "Design structure failed validation")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {"structural_validation": "passed", "static_html": fmt == "html",
                        "interactive_prototype": False, "browser_test": "not_run",
                        "accessibility_audit": "not_run", "source_verification": "not_run",
                        "human_review": "not_run"}
            if export_root is not None:
                path, digest = (export_html(content, export_root, filename) if fmt == "html"
                                else export_markdown(content, export_root, filename))
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "design", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in {ArtifactState.FAILED, ArtifactState.EXPORTED}:
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
