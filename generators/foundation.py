"""Dependency-free /INTEL G0 contracts. No external provider integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath
import re
from typing import Callable, Mapping


class IntelError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message

    def as_result(self) -> dict:
        return {"ok": False, "error": {"code": self.code, "message": self.message}}


class State(str, Enum):
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class Permission(str, Enum):
    READ_EXTERNAL = "read_external_sources"
    READ_LOCAL = "read_local_files"
    CREATE = "create_artifacts"
    MODIFY = "modify_artifacts"
    REPO_WRITE = "write_repositories"
    EXTERNAL = "invoke_external_services"
    PUBLISH = "publish_or_deploy"
    EXECUTE = "execute_code"
    BILLABLE = "billable_operations"


@dataclass(frozen=True)
class Capability:
    identifier: str
    command: str
    description: str
    category: str
    inputs: tuple[str, ...]
    formats: tuple[str, ...]
    schema: Mapping[str, str]
    required_tools: tuple[str, ...]
    permissions: frozenset[Permission]
    risk: str
    state: State = State.PLANNED
    fallback: str = "capability unavailable"
    version: str = "0.1.0"
    implemented: bool = False
    aliases: tuple[str, ...] = ()

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", self.identifier):
            raise ValueError("invalid capability identifier")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", self.command):
            raise ValueError("invalid capability command")
        if self.risk not in {"low", "medium", "high"}:
            raise ValueError("invalid risk")
        if not self.formats or not self.inputs or not self.schema:
            raise ValueError("inputs, formats and schema are required")
        if self.state == State.AVAILABLE and not self.implemented:
            raise ValueError("unimplemented capabilities cannot be available")
        if self.state == State.IMPLEMENTED and not self.implemented:
            raise ValueError("implemented state requires implementation")


class Registry:
    def __init__(self, capabilities=()):
        self._ids: dict[str, Capability] = {}
        self._commands: dict[str, Capability] = {}
        for capability in capabilities:
            self.register(capability)

    def register(self, capability: Capability) -> None:
        if capability.identifier in self._ids:
            raise ValueError("duplicate capability identifier")
        commands = (capability.command, *capability.aliases)
        normalized = [x.upper() for x in commands]
        if len(set(normalized)) != len(normalized) or any(x in self._commands for x in normalized):
            raise ValueError("conflicting capability command")
        self._ids[capability.identifier] = capability
        for command in normalized:
            self._commands[command] = capability

    def resolve(self, command: str) -> Capability:
        capability = self._commands.get(command.strip().upper())
        if capability is None:
            raise IntelError("UNKNOWN_GENERATOR", "Unknown generator type. Use /INTEL HELP.")
        return capability

    def all(self) -> tuple[Capability, ...]:
        return tuple(self._ids.values())


GENERATOR_TYPES = (
    ("PROMPT", "prompt", "markdown", "text"),
    ("CONCEPT", "concept", "markdown", "text"),
    ("DOCUMENT", "document", "markdown", "document"),
    ("IMAGE", "image", "png", "image"),
    ("DESIGN", "design", "svg", "design"),
    ("THEME", "theme", "json", "design"),
    ("BRAND", "brand", "svg", "design"),
    ("GIF", "motion", "gif", "animation"),
    ("SLIDES", "slides", "pptx", "document"),
    ("DIAGRAM", "diagram", "svg", "diagram"),
    ("CHART", "chart", "svg", "visualization"),
    ("CODE", "code", "text", "code"),
    ("VIDEO", "video", "mp4", "animation"),
    ("AUDIO", "audio", "wav", "audio"),
    ("WORKFLOW", "workflow", "json", "text"),
    ("PACK", "pack", "zip", "document"),
)


def default_registry() -> Registry:
    return Registry(Capability(
        identifier=name.lower(), command=name,
        description=f"Planned {name.lower()} generator", category=category,
        inputs=("text", "source_reference"), formats=(fmt,),
        schema={"objective": "nonempty string", "format": "supported output format"},
        required_tools=(), permissions=frozenset({Permission.CREATE}),
        risk="medium", state=State.PLANNED,
    ) for name, category, fmt, _ in GENERATOR_TYPES)


LEGACY = frozenset({"HELP", "STATUS", "QUERY", "RESEARCH", "DESIGN", "UI", "REVIEW", "SOURCE"})
NEEDS_TEXT = frozenset({"QUERY", "RESEARCH", "DESIGN", "UI", "REVIEW", "SOURCE"})


@dataclass(frozen=True)
class Command:
    name: str
    argument: str = ""
    generator: str | None = None


def parse_command(raw: str) -> Command:
    if not isinstance(raw, str) or not raw.strip():
        raise IntelError("INVALID_COMMAND", "Expected /INTEL [HELP|STATUS|QUERY|RESEARCH|DESIGN|UI|REVIEW|SOURCE|GENERATE].")
    matched = re.fullmatch(r"\s*/intel(?:\s+(.*?))?\s*", raw, re.I | re.S)
    if not matched:
        raise IntelError("INVALID_COMMAND", "Commands must start with /INTEL.")
    rest = (matched.group(1) or "").strip()
    if not rest:
        return Command("HELP")
    token, _, tail = rest.partition(" ")
    token = token.rstrip(":").upper()
    tail = tail.strip()
    if token == "GENERATE":
        parts = tail.split(None, 1)
        if not parts:
            raise IntelError("USAGE", "Usage: /INTEL GENERATE <TYPE> [brief]")
        name = parts[0].rstrip(":").upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            raise IntelError("USAGE", "Invalid generator type. Use /INTEL HELP.")
        return Command("GENERATE", parts[1].strip() if len(parts) > 1 else "", name)
    if token in LEGACY:
        if token in {"HELP", "STATUS"} and tail:
            raise IntelError("USAGE", f"Usage: /INTEL {token}")
        if token in NEEDS_TEXT and not tail:
            raise IntelError("USAGE", f"Usage: /INTEL {token}: <text>")
        return Command(token, tail)
    # Existing plain /INTEL <question> shorthand: only clearly non-command phrases.
    if rest.endswith("?") or (" " in rest and token not in {"GENERATE"}):
        return Command("QUERY", rest)
    raise IntelError("UNKNOWN_COMMAND", "Unknown /INTEL command. Use /INTEL HELP.")


@dataclass(frozen=True)
class Authorization:
    """Caller-controlled grant; never constructed from source or generated content."""
    granted: frozenset[Permission] = frozenset()

    def require(self, required: frozenset[Permission]) -> None:
        missing = required - self.granted
        if missing:
            raise IntelError("PERMISSION_DENIED", "Denied permissions: " + ", ".join(sorted(x.value for x in missing)))


@dataclass(frozen=True)
class ToolDeclaration:
    identifier: str
    capabilities: frozenset[str]
    reachable: bool = False
    verified: bool = False

    def __post_init__(self):
        if self.verified and not self.reachable:
            raise ValueError("verified tool must be reachable")


class ToolResolver:
    """Only explicit host-supplied evidence is accepted; no probing or invented endpoints."""
    def __init__(self, tools: Mapping[str, ToolDeclaration] | None = None):
        self.tools = dict(tools or {})

    def require(self, identifiers: tuple[str, ...]) -> None:
        for identifier in identifiers:
            tool = self.tools.get(identifier)
            if tool is None or not tool.reachable or not tool.verified:
                raise IntelError("TOOL_UNAVAILABLE", f"Tool {identifier} is missing or unverified")


@dataclass(frozen=True)
class Adapter:
    identifier: str
    kind: str
    invoke: Callable[[Mapping[str, object]], object]
    required_permissions: frozenset[Permission] = frozenset()
    max_attempts: int = 1

    def __post_init__(self):
        if self.max_attempts != 1:
            raise ValueError("G0 adapters are single-attempt only")


ADAPTER_KINDS = frozenset({"text", "image", "document", "design", "animation", "diagram", "code"})


def safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\ " in value or "\\" in value or "\x00" in value:
        raise IntelError("INVALID_PATH", "Invalid output path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"..", "."} for part in value.split("/")) or ":" in value or "//" in value:
        raise IntelError("INVALID_PATH", "Path must be canonical and relative")
    return str(path)


def verify_file(root: Path, name: str) -> bool:
    """Do not follow symlinks, including intermediate directories."""
    relative = safe_relative_path(name)
    base = root.resolve(strict=True)
    target = base
    for part in PurePosixPath(relative).parts:
        target = target / part
        if target.is_symlink():
            return False
    try:
        resolved = target.resolve(strict=True)
        return resolved.is_relative_to(base) and resolved.is_file() and resolved.stat().st_size > 0
    except (OSError, ValueError):
        return False


class Coordinator:
    """Pure deterministic boundary. Legacy commands are not executed by this package."""
    def __init__(self, registry: Registry | None = None, tools: ToolResolver | None = None,
                 adapters: Mapping[str, Adapter] | None = None):
        self.registry = registry if registry is not None else default_registry()
        self.tools = tools if tools is not None else ToolResolver()
        self.adapters = dict(adapters or {})
        self.audit: list[dict] = []

    def dispatch(self, raw: str, authorization: Authorization | None = None,
                 request: Mapping[str, object] | None = None) -> dict:
        try:
            command = parse_command(raw)
            if command.name == "HELP":
                return {"ok": True, "command": "HELP", "legacy": sorted(LEGACY),
                        "generators": [{"type": x.command, "state": x.state.value} for x in self.registry.all()]}
            if command.name == "STATUS":
                return {"ok": True, "command": "STATUS", "runtime": "local G0 contracts only",
                        "connected": False}
            if command.name != "GENERATE":
                return {"ok": False, "command": command.name,
                        "error": {"code": "HOST_REQUIRED", "message": "Legacy command requires a configured ChatGPT host."}}
            capability = self.registry.resolve(command.generator or "")
            # Validate before permissions, but never trust request-provided grants.
            data = dict(request or {})
            fmt = data.get("format", capability.formats[0])
            if not isinstance(fmt, str) or fmt.lower() not in capability.formats:
                raise IntelError("UNSUPPORTED_FORMAT", "Supported formats: " + ", ".join(capability.formats))
            if not capability.implemented or capability.state != State.AVAILABLE:
                raise IntelError("CAPABILITY_UNAVAILABLE", f"{capability.command} is {capability.state.value}; no generator executed.")
            objective = data.get("objective", command.argument)
            if not isinstance(objective, str) or not objective.strip() or len(objective) > 8192:
                raise IntelError("INVALID_REQUEST", "Objective must be 1-8192 characters.")
            (authorization or Authorization()).require(capability.permissions)
            self.tools.require(capability.required_tools)
            adapter = self.adapters.get(capability.identifier)
            if adapter is None or adapter.kind not in ADAPTER_KINDS:
                raise IntelError("ADAPTER_UNAVAILABLE", "No validated adapter registered")
            (authorization or Authorization()).require(adapter.required_permissions)
            try:
                output = adapter.invoke({"objective": objective, "format": fmt})
            except Exception:
                raise IntelError("ADAPTER_FAILED", "Adapter execution failed") from None
            # Output is unverified, even after a mock adapter returns.
            return {"ok": True, "verified": False, "output": output, "capability": capability.identifier}
        except IntelError as exc:
            self.audit.append({"event": "dispatch_denied", "code": exc.code})
            return exc.as_result()
