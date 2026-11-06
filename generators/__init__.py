"""G0 deterministic contracts, not a ChatGPT-native slash-command integration."""
from .foundation import (
    Adapter, ADAPTER_KINDS, Authorization, Capability, Command, Coordinator,
    GENERATOR_TYPES, IntelError, Permission, Registry, State, ToolDeclaration,
    ToolResolver, default_registry, parse_command, safe_relative_path, verify_file,
)
from .artifacts import ArtifactManifest, ArtifactState, GenerationRequest

__all__ = [
    "Adapter", "ADAPTER_KINDS", "Authorization", "Capability", "Command",
    "Coordinator", "GENERATOR_TYPES", "IntelError", "Permission", "Registry",
    "State", "ToolDeclaration", "ToolResolver", "default_registry",
    "parse_command", "safe_relative_path", "verify_file", "ArtifactManifest",
    "ArtifactState", "GenerationRequest",
]

from .text_runtime import TextRuntime, text_registry, validate_request, render_markdown

__all__ += ["TextRuntime", "text_registry", "validate_request", "render_markdown"]

from .model_host import OpenAIResponsesHost, ModelOutput
__all__ += ["OpenAIResponsesHost", "ModelOutput"]

from .ollama_host import OllamaLocalHost
from .provider_router import ProviderRouter, PROVIDERS
__all__ += ["OllamaLocalHost", "ProviderRouter", "PROVIDERS"]
