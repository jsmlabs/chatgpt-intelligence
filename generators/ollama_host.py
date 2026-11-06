"""Optional local Ollama adapter. Fixed loopback, bounded responses, no redirects."""
from __future__ import annotations

import json
import os
import re
import socket
import urllib.error
import urllib.request

from .artifacts import GenerationRequest
from .foundation import IntelError
from .model_host import MAX_MODEL_OUTPUT_CHARS, ModelOutput, SYSTEM_INSTRUCTIONS

ORIGIN = "http://127.0.0.1:11434"
MAX_RESPONSE_BYTES = 262144


class OllamaLocalHost:
    def __init__(self, *, model: str | None = None, timeout: float = 60.0,
                 max_output_tokens: int = 4096):
        self.model = model if model is not None else os.environ.get("INTEL_OLLAMA_MODEL", "")
        if (not isinstance(self.model, str) or isinstance(timeout, bool)
                or not isinstance(timeout, (float, int)) or not 1 <= timeout <= 120
                or isinstance(max_output_tokens, bool) or not isinstance(max_output_tokens, int)
                or not 128 <= max_output_tokens <= 8192):
            raise ValueError("Invalid local model configuration")
        self.timeout, self.max_output_tokens = timeout, max_output_tokens

    @property
    def configured(self) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", self.model))

    def _request(self, req: urllib.request.Request, timeout: float) -> dict:
        try:
            with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise IntelError("MODEL_RESPONSE_INVALID", "Local model response is too large")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Invalid local response")
            return data
        except IntelError:
            raise
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, ValueError):
            raise IntelError("MODEL_REQUEST_FAILED", "Local model request failed") from None

    def available(self) -> bool:
        """Explicit read-only readiness probe, invoked only after permission gate."""
        if not self.configured:
            return False
        try:
            data = self._request(urllib.request.Request(ORIGIN + "/api/tags", method="GET"),
                                 min(self.timeout, 3.0))
            models = data.get("models")
            return isinstance(models, list) and any(
                isinstance(x, dict) and x.get("name") == self.model for x in models)
        except IntelError:
            return False

    def generate(self, kind: str, brief: GenerationRequest) -> ModelOutput:
        if not self.configured:
            raise IntelError("MODEL_UNAVAILABLE", "Local model is not configured")
        if kind not in {"PROMPT", "CONCEPT", "DOCUMENT"}:
            raise IntelError("CAPABILITY_UNAVAILABLE", "Unsupported local model generator")
        content = json.dumps({
            "generator": kind, "objective": brief.objective, "audience": brief.audience,
            "style": brief.style, "sources_unverified": list(brief.sources),
            "constraints": list(brief.constraints), "verification_requirements": list(brief.verification),
            "format": "markdown",
        }, ensure_ascii=False)
        body = {"model": self.model, "system": SYSTEM_INSTRUCTIONS, "prompt": content,
                "stream": False, "options": {"num_predict": self.max_output_tokens}}
        req = urllib.request.Request(
            ORIGIN + "/api/generate", method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"))
        result = self._request(req, self.timeout)
        output = result.get("response")
        if (result.get("done") is not True or not isinstance(output, str)
                or not output.strip() or len(output) > MAX_MODEL_OUTPUT_CHARS):
            raise IntelError("MODEL_RESPONSE_INVALID", "Local model response failed validation")
        return ModelOutput(output.strip(), "ollama-local", self.model, "")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None
