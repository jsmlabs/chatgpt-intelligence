"""Local MCP stdio host for the INTEL text generators.

Implements a bounded JSON-RPC 2.0 subset of MCP 2025-11-25 / 2025-06-18:
initialize, notifications/initialized, ping, tools/list, tools/call.
No HTTP listener, filesystem export or implicit model permissions.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, BinaryIO

from .foundation import Authorization, Permission, IntelError
from .model_host import OpenAIResponsesHost
from .ollama_host import OllamaLocalHost
from .provider_router import ProviderRouter
from .text_runtime import TextRuntime

MAX_INPUT_LINE = 32768
SUPPORTED_VERSIONS = frozenset({"2025-06-18", "2025-11-25"})
TOOL_TYPES = {"generate_prompt": "PROMPT", "generate_concept": "CONCEPT",
              "generate_document": "DOCUMENT"}
DESCRIPTION = {
    "generate_prompt": "Generate an editable Markdown prompt draft.",
    "generate_concept": "Generate an editable Markdown concept brief.",
    "generate_document": "Generate an editable Markdown document draft.",
}
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "objective": {"type": "string", "minLength": 1, "maxLength": 8192},
        "audience": {"type": "string", "maxLength": 512},
        "style": {"type": "string", "maxLength": 512},
        "sources": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "constraints": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "verification": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 1024}},
        "format": {"type": "string", "enum": ["markdown"]},
        "mode": {"type": "string", "enum": ["template", "model"]},
        "provider": {"type": "string", "enum": ["template", "ollama-local",
                                                   "chatgpt-host", "openai-api"]},
    },
    "required": ["objective"],
    "additionalProperties": False,
}


class MCPHost:
    def __init__(self, authorization: Authorization | None = None,
                 model_host: OpenAIResponsesHost | None = None,
                 provider_router: ProviderRouter | None = None):
        self.authorization = authorization or Authorization()
        self.runtime = TextRuntime(model_host=model_host, provider_router=provider_router)
        self.initialized = False

    def handle(self, message: Any) -> dict | None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error(None, -32600, "Invalid JSON-RPC request")
        method = message.get("method")
        request_id = message.get("id")
        if isinstance(request_id, (bool, dict, list)) or not (
            request_id is None or isinstance(request_id, (str, int))
        ):
            return self._error(None, -32600, "Invalid JSON-RPC request id")
        if not isinstance(method, str) or "result" in message or "error" in message:
            return self._error(request_id, -32600, "Invalid JSON-RPC method")
        if method == "notifications/initialized" and request_id is None:
            return None
        if request_id is None:
            # Ignore notifications and never execute side effects from them.
            return None
        params = message.get("params", {})
        if not isinstance(params, dict):
            return self._error(request_id, -32602, "Invalid parameters")
        if method == "initialize":
            version = params.get("protocolVersion")
            if version not in SUPPORTED_VERSIONS:
                version = "2025-11-25"
            self.initialized = True
            return self._ok(request_id, {
                "protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "chatgpt-intelligence", "version": "0.3.0"},
            })
        if not self.initialized:
            return self._error(request_id, -32002, "Initialize MCP connection first")
        if method == "ping":
            return self._ok(request_id, {})
        if method == "tools/list":
            return self._ok(request_id, {"tools": [
                {"name": name, "description": DESCRIPTION[name],
                 "inputSchema": INPUT_SCHEMA} for name in TOOL_TYPES
            ]})
        if method == "tools/call":
            name, arguments = params.get("name"), params.get("arguments", {})
            if name not in TOOL_TYPES:
                return self._error(request_id, -32602, "Unknown INTEL tool")
            if not isinstance(arguments, dict):
                return self._error(request_id, -32602, "Tool arguments must be an object")
            mode = arguments.get("mode", "template")
            if not isinstance(mode, str) or mode not in ("template", "model"):
                return self._error(request_id, -32602, "Invalid execution mode")
            provider = arguments.get("provider")
            brief = {key: value for key, value in arguments.items()
                     if key not in {"mode", "provider"}}
            result = self.runtime.execute(
                "/INTEL GENERATE " + TOOL_TYPES[name],
                request=brief, authorization=self.authorization, mode=mode, provider=provider,
            )
            if not result["ok"]:
                error = result["error"]
                return self._ok(request_id, {
                    "content": [{"type": "text", "text": json.dumps(error, sort_keys=True)}],
                    "isError": True,
                })
            manifest = result["manifest"]
            return self._ok(request_id, {
                "content": [{"type": "text", "text": result["content"]}],
                "structuredContent": {
                    "artifact_id": manifest.identifier,
                    "capability": manifest.capability,
                    "version": manifest.version,
                    "state": manifest.state.value,
                    "output_verified": manifest.output_verified,
                    "provenance": manifest.provenance,
                    "verification": result["evidence"],
                },
                "isError": False,
            })
        return self._error(request_id, -32601, "Method not found")

    @staticmethod
    def _ok(request_id: str | int, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: str | int | None, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": request_id,
                "error": {"code": code, "message": message}}


def serve(host: MCPHost, source: BinaryIO, sink: BinaryIO) -> None:
    while True:
        line = source.readline(MAX_INPUT_LINE + 1)
        if not line:
            return
        if len(line) > MAX_INPUT_LINE:
            # Drain oversized request without buffering it or evaluating any content.
            while line and not line.endswith(b"\n"):
                line = source.readline(MAX_INPUT_LINE + 1)
            reply = MCPHost._error(None, -32700, "Request exceeds transport size limit")
        else:
            try:
                message = json.loads(line)
            except (UnicodeError, ValueError):
                reply = MCPHost._error(None, -32700, "Invalid JSON")
            else:
                try:
                    reply = host.handle(message)
                except Exception:
                    # Never leak an arbitrary exception, token or source content.
                    reply = MCPHost._error(message.get("id") if isinstance(message, dict)
                                           and isinstance(message.get("id"), (str, int))
                                           else None, -32603, "Internal server error")
        if reply is not None:
            sink.write((json.dumps(reply, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8"))
            sink.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local MCP stdio host for INTEL")
    parser.add_argument("--model-timeout", type=float, default=60.0)
    parser.add_argument("--model-max-output-tokens", type=int, default=4096)
    parser.add_argument("--allow-create", action="store_true",
                        help="Trusted operator grant for draft creation")
    parser.add_argument("--allow-external", action="store_true",
                        help="Trusted operator grant for external service access")
    parser.add_argument("--allow-billable", action="store_true",
                        help="Trusted operator grant for billable model calls")
    args = parser.parse_args(argv)
    granted: set[Permission] = set()
    if args.allow_create:
        granted.add(Permission.CREATE)
    if args.allow_external:
        granted.add(Permission.EXTERNAL)
    if args.allow_billable:
        granted.add(Permission.BILLABLE)
    if not 1 <= args.model_timeout <= 120 or not 128 <= args.model_max_output_tokens <= 8192:
        parser.error("Model timeout must be 1-120 seconds and tokens 128-8192")
    host = MCPHost(Authorization(frozenset(granted)),
                   provider_router=ProviderRouter(
                       ollama_host=OllamaLocalHost(timeout=args.model_timeout,
                                                   max_output_tokens=args.model_max_output_tokens),
                       openai_host=OpenAIResponsesHost(timeout=args.model_timeout,
                                                       max_output_tokens=args.model_max_output_tokens)))
    serve(host, sys.stdin.buffer, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
