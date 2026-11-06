"""G2.1 IMAGE production briefs, not raster generation.

No network access, image renderer or billable provider is invoked.
A brief is an editable Markdown artifact, never a PNG or verified image.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Mapping
from uuid import uuid4

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission, State, default_registry, parse_command
from .text_runtime import (
    MAX_OUTPUT, _check_markdown, _inline, _items, _require_text,
    _unwrap_model_fence, export_markdown, validate_request,
)

RATIOS = frozenset({"1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16"})
IMAGE_FIELDS = frozenset({"aspect_ratio", "palette"})
PROVENANCE = (
    "\n\n## Provenance and limitations\n\n"
    "Image production brief only. No raster image was generated, fetched, "
    "saved or verified. Source references and content claims are unverified; "
    "this is an editable draft, not an approved finished image.\n"
)
CLIENT_PROVENANCE = (
    "\n\n## Provenance and limitations\n\n"
    "Client-submitted image brief; model identity is not attested. "
    "No raster image was generated, fetched, saved or verified by INTEL. "
    "Source references and factual claims are unverified.\n"
)


def image_capability():
    cap = default_registry().resolve("IMAGE")
    return replace(cap, implemented=True, state=State.AVAILABLE,
                   formats=("markdown",), required_tools=(), risk="low",
                   version="0.1.0", description="Offline IMAGE production brief (not image generation)")


def validate_image_request(argument: str, values: Mapping[str, object] | None):
    if values is None:
        values = {}
    if not isinstance(values, Mapping):
        raise IntelError("INVALID_REQUEST", "Image request must be an object")
    aspect = _require_text(values.get("aspect_ratio", "1:1"), "aspect_ratio", required=True, limit=16)
    if aspect not in RATIOS:
        raise IntelError("INVALID_REQUEST", "Unsupported aspect_ratio")
    palette = _require_text(values.get("palette", ""), "palette", limit=512)
    basic = {k: v for k, v in values.items() if k not in IMAGE_FIELDS}
    brief = validate_request(argument, basic)
    return brief, aspect, palette


def render_image_brief(brief, aspect: str, palette: str) -> str:
    objective = _inline(brief.objective)
    audience = _inline(brief.audience)
    style = _inline(brief.style or "User-defined; avoid inventing brand references")
    colors = _inline(palette or "No fixed palette supplied")
    constraints = "\n".join("- " + _inline(x) for x in brief.constraints) or "- None supplied"
    references = "\n".join("- " + _inline(x) for x in brief.sources) or "- None supplied"
    checks = "\n".join("- " + _inline(x) for x in brief.verification) or "- Structural checks only"
    return (
        "# Image Production Brief\n\n"
        "## Objective and audience\n\n"
        "- Objective: " + objective + "\n"
        "- Audience: " + audience + "\n"
        "- Intended output: Image production brief, not an image file\n\n"
        "## Creative direction\n\n"
        "- Style: " + style + "\n"
        "- Palette: " + colors + "\n"
        "- Aspect ratio: " + aspect + "\n\n"
        "## Composition\n\n"
        "- Subject and focal hierarchy: Derive from the objective, then confirm missing specifics.\n"
        "- Framing: Preserve safe cropping at the selected aspect ratio.\n"
        "- Lighting, textures and environment: Align with the declared visual style.\n\n"
        "## Reusable image prompt\n\n"
        "Create a visual for: " + objective + ". Intended audience: " + audience +
        ". Style: " + style + ". Color direction: " + colors +
        ". Aspect ratio: " + aspect + ". Prioritize coherent composition, readable "
        "visual hierarchy and realistic or deliberately stylized detail as appropriate. "
        "Do not add unsupported logos, text or factual claims.\n\n"
        "## Variants\n\n"
        "- A: Minimal subject-focused composition.\n"
        "- B: Environmental composition with added context, without changing core identity.\n\n"
        "## Constraints\n\n" + constraints + "\n\n"
        "## Unverified input references\n\n" + references + "\n\n"
        "## Review and verification\n\n" + checks + "\n"
        "- Inspect composition, rights, accessibility and any embedded text manually.\n"
        "- A separate approved image-capable host must render and verify actual image bytes.\n"
        + PROVENANCE
    )


class ImageRuntime:
    """Deterministic IMAGE brief creation and bounded client draft intake."""

    def __init__(self):
        self.capability = image_capability()

    def execute(self, raw: str, *, request: Mapping[str, object] | None = None,
                authorization: Authorization | None = None, draft: object = None,
                export_root: Path | None = None, filename: str | None = None,
                provider: str | None = None, mode: str = "template") -> dict:
        manifest = None
        try:
            cmd = parse_command(raw)
            if cmd.name != "GENERATE" or cmd.generator != "IMAGE":
                raise IntelError("INVALID_COMMAND", "Expected /INTEL GENERATE IMAGE")
            brief, aspect, palette = validate_image_request(cmd.argument, request)
            (authorization or Authorization()).require(frozenset({Permission.CREATE}))
            if mode != "template" or provider not in (None, "template"):
                raise IntelError("CAPABILITY_UNAVAILABLE",
                                 "G2.1 does not have a verified image renderer or model provider")
            if (export_root is None) != (filename is None):
                raise IntelError("INVALID_REQUEST", "Export requires root and filename together")
            if draft is not None:
                if not isinstance(draft, str) or not draft.strip() or "\x00" in draft:
                    raise IntelError("INVALID_REQUEST", "Nonempty bounded Markdown image brief required")
                try:
                    if len(draft.encode("utf-8")) > MAX_OUTPUT - len(CLIENT_PROVENANCE.encode("utf-8")) - 32:
                        raise IntelError("INVALID_REQUEST", "Image draft exceeds size limit")
                except UnicodeError:
                    raise IntelError("INVALID_REQUEST", "Image draft contains invalid Unicode") from None
            manifest = ArtifactManifest(
                uuid4().hex, "text/markdown", "1.0", brief.sources, self.capability.identifier)
            manifest.created_at = datetime.now(timezone.utc).isoformat()
            manifest.provenance = {
                "producer": "client-submitted-draft" if draft is not None else "local-deterministic-template",
                "model_provider": "not-attested" if draft is not None else "not-used",
                "source_status": "unverified", "renderer_version": self.capability.version,
                "artifact_kind": "image-production-brief",
            }
            manifest.transition(ArtifactState.READY)
            manifest.transition(ArtifactState.GENERATING)
            if draft is None:
                content = render_image_brief(brief, aspect, palette)
            else:
                normalized = _unwrap_model_fence(draft.strip())
                if normalized == draft.strip() and re.match(
                        r"^ {0,3}`{3,}(?:markdown|md)?[ \t]*$", draft.strip().splitlines()[0], re.I):
                    raise IntelError("VALIDATION_FAILED", "Ambiguous outer Markdown code fence")
                if not re.match(r"^#\s+\S", normalized):
                    normalized = "# Image Production Brief\n\n" + normalized
                content = normalized + CLIENT_PROVENANCE
            manifest.transition(ArtifactState.VALIDATING)
            manifest.validations = _check_markdown(content)
            if not all(manifest.validations.values()):
                raise IntelError("VALIDATION_FAILED", "Image brief failed structural checks")
            manifest.transition(ArtifactState.REVIEWED)
            evidence = {
                "structural_validation": "passed",
                "image_generated": False, "image_verified": False,
                "llm_generation": "not_attested" if draft is not None else "not_run",
                "source_verification": "not_run", "human_review": "not_run",
            }
            if export_root is not None:
                path, digest = export_markdown(content, export_root, filename)
                manifest.record_verified_output(path, export_root)
                manifest.transition(ArtifactState.EXPORTED, output_verified=True)
                evidence["file_sha256"] = digest
            return {"ok": True, "capability": "image", "content": content,
                    "manifest": manifest, "evidence": evidence, "verified": False}
        except IntelError as exc:
            if manifest is not None and manifest.state not in {ArtifactState.FAILED, ArtifactState.EXPORTED}:
                manifest.transition(ArtifactState.FAILED)
            return {**exc.as_result(), "manifest": manifest}
