"""Typed artifact requests, manifests and state transitions for G0."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from .foundation import verify_file
from .foundation import IntelError


@dataclass(frozen=True)
class GenerationRequest:
    objective: str
    audience: str
    sources: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    style: str = ""
    output_format: str = "markdown"
    verification: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.objective, str) or not self.objective.strip() or len(self.objective) > 8192:
            raise ValueError("objective required, maximum 8192 characters")
        if not isinstance(self.audience, str) or not self.audience.strip():
            raise ValueError("audience required")


class ArtifactState(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    GENERATING = "generating"
    VALIDATING = "validating"
    REVIEWED = "reviewed"
    EXPORTED = "exported"
    BLOCKED = "blocked"
    FAILED = "failed"


TRANSITIONS = {
    ArtifactState.PLANNED: frozenset({ArtifactState.READY, ArtifactState.BLOCKED, ArtifactState.FAILED}),
    ArtifactState.READY: frozenset({ArtifactState.GENERATING, ArtifactState.BLOCKED, ArtifactState.FAILED}),
    ArtifactState.GENERATING: frozenset({ArtifactState.VALIDATING, ArtifactState.FAILED, ArtifactState.BLOCKED}),
    ArtifactState.VALIDATING: frozenset({ArtifactState.REVIEWED, ArtifactState.FAILED, ArtifactState.BLOCKED}),
    ArtifactState.REVIEWED: frozenset({ArtifactState.EXPORTED, ArtifactState.FAILED, ArtifactState.BLOCKED}),
    ArtifactState.BLOCKED: frozenset({ArtifactState.READY, ArtifactState.FAILED}),
    ArtifactState.FAILED: frozenset(),
    ArtifactState.EXPORTED: frozenset(),
}


@dataclass
class ArtifactManifest:
    identifier: str
    artifact_type: str
    version: str
    source_references: tuple[str, ...]
    capability: str
    content_reference: str | None = None
    validations: dict[str, bool] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    state: ArtifactState = ArtifactState.PLANNED
    parent_revision: str | None = None
    output_verified: bool = False
    _verified_root: Path | None = field(default=None, repr=False)
    history: list[str] = field(default_factory=list)

    def transition(self, next_state: ArtifactState, *, output_verified: bool = False) -> None:
        if next_state not in TRANSITIONS[self.state]:
            raise IntelError("INVALID_TRANSITION", f"{self.state.value} -> {next_state.value} denied")
        if next_state == ArtifactState.REVIEWED and (not self.validations or not all(self.validations.values())):
            raise IntelError("VALIDATION_FAILED", "Validation results have not passed")
        if next_state == ArtifactState.EXPORTED:
            if not output_verified or not self.content_reference or not self.output_verified or self._verified_root is None or not verify_file(self._verified_root, self.content_reference):
                raise IntelError("EXPORT_UNVERIFIED", "Output must be independently verified before export")
        self.history.append(f"{self.state.value}->{next_state.value}")
        self.state = next_state

    def record_verified_output(self, reference: str, root: Path) -> None:
        if self.state != ArtifactState.REVIEWED:
            raise IntelError("INVALID_TRANSITION", "Output verification requires reviewed state")
        if not isinstance(root, Path) or not verify_file(root, reference):
            raise IntelError("EXPORT_UNVERIFIED", "Output file missing, empty or unsafe")
        self.content_reference, self.output_verified = reference, True
        self._verified_root = root

    def revise(self, new_identifier: str, new_version: str) -> "ArtifactManifest":
        if not new_identifier or new_identifier == self.identifier or not new_version or new_version == self.version:
            raise IntelError("INVALID_REVISION", "New revision must have distinct id and version")
        return ArtifactManifest(
            identifier=new_identifier, artifact_type=self.artifact_type, version=new_version,
            source_references=self.source_references, capability=self.capability,
            provenance=dict(self.provenance), parent_revision=self.identifier,
        )
