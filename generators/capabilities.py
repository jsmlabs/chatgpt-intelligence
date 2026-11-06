"""Passive runtime capability catalog; never a dispatch or authorization bypass.

The legacy /INTEL planned registry in foundation.py remains unchanged.
This catalog describes only the 10 implemented local CLI generator entrypoints.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .foundation import Authorization, Permission
from .provider_router import PROVIDERS, ProviderRouter

@dataclass(frozen=True)
class GeneratorSpec:
    name: str
    formats: tuple[str, ...]
    providers: tuple[str, ...]
    description: str
    default_format: str
    permission: Permission = Permission.CREATE

    def __post_init__(self) -> None:
        if not self.name or not self.formats or self.default_format not in self.formats:
            raise ValueError("Invalid generator capability specification")
        if not set(self.providers).issubset(PROVIDERS):
            raise ValueError("Unknown provider in capability specification")

    def summary(self) -> dict[str, object]:
        return {
            "name": self.name,
            "state": "implemented",
            "formats": list(self.formats),
            "default_format": self.default_format,
            "providers": list(self.providers),
            "required_permissions": [self.permission.value],
            "execution_verified": False,
            "description": self.description,
        }

# These describe interfaces rather than asserting that an optional model or
# external renderer has been reached. Generation retains runtime validation.
_SPECS = (
    GeneratorSpec("prompt", ("markdown",), PROVIDERS, "Structured prompt draft", "markdown"),
    GeneratorSpec("concept", ("markdown",), PROVIDERS, "Structured concept brief", "markdown"),
    GeneratorSpec("document", ("markdown",), PROVIDERS, "Structured document draft", "markdown"),
    GeneratorSpec("image", ("markdown", "json", "png"), ("template",),
                  "Production brief or local procedural image; semantic rendering is opt-in elsewhere", "markdown"),
    GeneratorSpec("design", ("markdown", "json", "html"), ("template",),
                  "Design brief or inert HTML/CSS prototype", "markdown"),
    GeneratorSpec("theme", ("json", "css"), ("template",),
                  "Validated color tokens and CSS", "json"),
    GeneratorSpec("brand", ("markdown", "json", "svg"), ("template",),
                  "Brand brief and local SVG directions", "markdown"),
    GeneratorSpec("gif", ("json", "gif"), ("template",),
                  "Motion storyboard or procedural animated GIF", "json"),
    GeneratorSpec("slides", ("json", "pptx"), ("template",),
                  "Slide storyboard or editable PPTX export", "json"),
    GeneratorSpec("diagram", ("json", "mermaid", "svg"), ("template",),
                  "Directed graph structure, Mermaid or SVG", "json"),
)
GENERATORS: Mapping[str, GeneratorSpec] = MappingProxyType({s.name: s for s in _SPECS})
GENERATOR_NAMES: tuple[str, ...] = tuple(GENERATORS)

if len(GENERATORS) != len(_SPECS):
    raise ValueError("Duplicate runtime generator")


def generators_report() -> dict[str, dict[str, object]]:
    """No file, network, process, key, provider or tool access."""
    return {name: spec.summary() for name, spec in GENERATORS.items()}


def providers_report(router: ProviderRouter | None = None,
                     authorization: Authorization | None = None) -> dict[str, dict[str, object]]:
    """Use the actual router's passive detection contract, with no probes."""
    instance = router if router is not None else ProviderRouter()
    detected = instance.detect(authorization)
    required = {
        "template": (Permission.CREATE,),
        "ollama-local": (Permission.CREATE, Permission.EXTERNAL),
        "chatgpt-host": (Permission.CREATE,),
        "openai-api": (Permission.CREATE, Permission.EXTERNAL, Permission.BILLABLE),
    }
    descriptions = {
        "template": "Deterministic local generation; no network",
        "ollama-local": "Optional local Ollama model; reachability not tested",
        "chatgpt-host": "Host-injected adapter; not available in standalone CLI",
        "openai-api": "Optional explicitly authorized billable API",
    }
    return {
        name: {
            "configured": bool(detected[name]["configured"]),
            "authorized": bool(detected[name]["authorized"]),
            "verified": bool(detected[name]["verified"]),
            "state": ("available" if detected[name]["verified"] and detected[name]["configured"]
                      else "configured_unverified" if detected[name]["configured"]
                      else "not_configured"),
            "billable": bool(detected[name]["billable"]),
            "required_permissions": [p.value for p in required[name]],
            "description": descriptions[name],
        } for name in PROVIDERS
    }


def capability_report(router: ProviderRouter | None = None,
                      authorization: Authorization | None = None) -> dict[str, object]:
    return {"schema_version": 1, "generators": generators_report(),
            "providers": providers_report(router, authorization),
            "permissions_are_grants": False,
            "execution_verification": "not_run"}
