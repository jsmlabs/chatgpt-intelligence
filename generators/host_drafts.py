"""G1.9 deterministic intake of client-submitted drafts, not a model API.

The caller supplies the draft text. This module neither invokes a model nor
attests which model or client produced the content. It preserves G0 creation,
artifact lifecycle and structural validation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Mapping

from .artifacts import ArtifactManifest, ArtifactState
from .foundation import Authorization, IntelError, Permission
from .text_runtime import (
    MAX_OUTPUT, TEXT_TYPES, _check_markdown, _prepare_model_markdown,
    text_registry, validate_request,
)

PROVENANCE_TEXT = (
    "\n\n## Provenance and limitations\n\n"
    "Client-submitted draft; its model origin, cited sources and factual claims "
    "were not independently verified. Structural validation does not imply "
    "human approval or an authenticated ChatGPT model invocation.\n"
)


def submit_host_draft(kind: str, *, request: Mapping[str, object],
                      content: object, authorization: Authorization | None = None) -> dict:
    """Validate untrusted client content without contacting any provider."""
    manifest: ArtifactManifest | None = None
    try:
        cap = text_registry().resolve(kind)
        if cap.command not in TEXT_TYPES:
            raise IntelError("CAPABILITY_UNAVAILABLE", "Host intake supports text generators only")
        brief = validate_request("", request)
        (authorization or Authorization()).require(frozenset({Permission.CREATE}))
        if not isinstance(content, str) or not content.strip():
            raise IntelError("INVALID_REQUEST", "Nonempty Markdown draft is required")
        try:
            size = len(content.encode("utf-8"))
        except UnicodeError:
            raise IntelError("INVALID_REQUEST", "Draft contains invalid Unicode") from None
        if not 0 < size <= MAX_OUTPUT:
            raise IntelError("INVALID_REQUEST", "Draft exceeds the maximum size")
        manifest = ArtifactManifest(
            identifier=uuid4().hex, artifact_type="text/markdown",
            version="1.0", source_references=brief.sources, capability=cap.identifier,
        )
        manifest.created_at = datetime.now(timezone.utc).isoformat()
        manifest.provenance = {
            "producer": "client-submitted-draft",
            "model_provider": "not-attested",
            "source_status": "unverified",
            "renderer_version": cap.version,
        }
        manifest.transition(ArtifactState.READY)
        manifest.transition(ArtifactState.GENERATING)
        output = _prepare_model_markdown(cap.command, content) + PROVENANCE_TEXT
        manifest.transition(ArtifactState.VALIDATING)
        manifest.validations = _check_markdown(output)
        if not all(manifest.validations.values()):
            raise IntelError("VALIDATION_FAILED", "Client-submitted Markdown failed structural checks")
        manifest.transition(ArtifactState.REVIEWED)
        return {
            "ok": True, "capability": cap.identifier, "content": output,
            "manifest": manifest, "verified": False,
            "evidence": {
                "structural_validation": "passed",
                "client_submission": "received",
                "llm_generation": "not_attested",
                "source_verification": "not_run",
                "human_review": "not_run",
            },
        }
    except IntelError as exc:
        if manifest is not None and manifest.state not in {ArtifactState.FAILED, ArtifactState.EXPORTED}:
            manifest.transition(ArtifactState.FAILED)
        return {**exc.as_result(), "manifest": manifest}
