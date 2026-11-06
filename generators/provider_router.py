"""Trusted provider routing. Does not infer client tools or permissions."""
from __future__ import annotations

from .foundation import Authorization, IntelError, Permission, ToolResolver

PROVIDERS = ("template", "ollama-local", "chatgpt-host", "openai-api")


class ProviderRouter:
    def __init__(self, *, ollama_host=None, chatgpt_host=None, openai_host=None,
                 host_tools: ToolResolver | None = None):
        self.ollama_host = ollama_host
        self.chatgpt_host = chatgpt_host
        self.openai_host = openai_host
        self.host_tools = host_tools or ToolResolver()

    def detect(self, authorization: Authorization | None = None) -> dict:
        """Passive capability report: no network access and no inferred verification."""
        grants = (authorization or Authorization()).granted
        return {
            "template": {"configured": True, "authorized": Permission.CREATE in grants,
                         "billable": False, "verified": True},
            "ollama-local": {
                "configured": bool(self.ollama_host and self.ollama_host.configured),
                "authorized": {Permission.CREATE, Permission.EXTERNAL} <= grants,
                "billable": False, "verified": False},
            "chatgpt-host": {
                "configured": bool(self.chatgpt_host and self.chatgpt_host.configured),
                "authorized": Permission.CREATE in grants,
                "billable": False,
                "verified": bool((t := self.host_tools.tools.get("chatgpt-host"))
                                 and t.reachable and t.verified)},
            "openai-api": {
                "configured": bool(self.openai_host and self.openai_host.configured),
                "authorized": {Permission.CREATE, Permission.EXTERNAL,
                               Permission.BILLABLE} <= grants,
                "billable": True, "verified": False},
        }

    def select(self, provider: str, grants: Authorization):
        if provider not in PROVIDERS:
            raise IntelError("INVALID_REQUEST", "Unknown execution provider")
        if provider == "template":
            return None
        if provider == "openai-api":
            grants.require(frozenset({Permission.EXTERNAL, Permission.BILLABLE}))
            host = self.openai_host
        elif provider == "ollama-local":
            grants.require(frozenset({Permission.EXTERNAL}))
            host = self.ollama_host
        else:
            host = self.chatgpt_host
            if host is not None and host.configured:
                self.host_tools.require(("chatgpt-host",))
        if host is None or not host.configured:
            raise IntelError("MODEL_UNAVAILABLE", "Selected provider is not configured")
        if provider == "ollama-local" and not host.available():
            raise IntelError("TOOL_UNAVAILABLE", "Local Ollama model is not installed or reachable")
        return host
