"""Bounded, opt-in AI agent capability orchestration.

This runtime does not execute a model, discover tools, or grant permissions.
Hosts supply handlers, authorization and optional telemetry explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import re
import time
from typing import Callable, Mapping

from .foundation import Authorization, IntelError, Permission

_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


class RetryableFailure(Exception):
    """Only idempotent handlers may raise this to request a retry."""


@dataclass(frozen=True)
class AgentCapability:
    name: str
    handler: Callable[[dict[str, object]], object]
    permissions: frozenset[Permission] = frozenset()
    idempotent: bool = False
    max_attempts: int = 1
    input_keys: frozenset[str] = frozenset()
    max_output_chars: int = 32768

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _NAME.fullmatch(self.name):
            raise ValueError("Invalid capability name")
        if not callable(self.handler):
            raise ValueError("Capability handler must be callable")
        if not isinstance(self.permissions, frozenset) or any(
            not isinstance(p, Permission) for p in self.permissions
        ):
            raise ValueError("Permissions must be explicit Permission values")
        if isinstance(self.max_attempts, bool) or not 1 <= self.max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3")
        if self.max_attempts > 1 and not self.idempotent:
            raise ValueError("Automatic retries require an idempotent capability")
        if not isinstance(self.input_keys, frozenset) or any(
            not isinstance(k, str) or not k or len(k) > 64 for k in self.input_keys
        ):
            raise ValueError("Invalid input contract")
        if not 1 <= self.max_output_chars <= 262144:
            raise ValueError("Invalid output limit")


class AgentRegistry:
    """Host-owned immutable-snapshot registry; no dynamic name inference."""

    def __init__(self, capabilities: tuple[AgentCapability, ...] = ()):
        self._entries: dict[str, AgentCapability] = {}
        for item in capabilities:
            self.register(item)

    def register(self, capability: AgentCapability) -> None:
        if not isinstance(capability, AgentCapability):
            raise TypeError("Expected AgentCapability")
        if capability.name in self._entries:
            raise ValueError("Duplicate capability")
        self._entries[capability.name] = capability

    def resolve(self, name: str) -> AgentCapability:
        if not isinstance(name, str) or name not in self._entries:
            raise IntelError("CAPABILITY_UNAVAILABLE", "Capability is not registered")
        return self._entries[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))


class AgentRuntime:
    """Deterministic policy boundary around untrusted capability output.

    No auto-discovery, implicit permission, network connection or shell execution.
    Telemetry contains capability, outcome, attempt count and elapsed time only.
    """

    def __init__(
        self, registry: AgentRegistry, *,
        observer: Callable[[dict[str, object]], None] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.registry = registry
        self.observer = observer
        self.sleeper = sleeper
        self.clock = clock

    def _emit(self, event: dict[str, object]) -> None:
        if self.observer is not None:
            try:
                self.observer(dict(event))
            except Exception:
                pass  # Observability cannot alter authorization or execution.

    def execute(
        self, name: str, payload: Mapping[str, object],
        *, authorization: Authorization | None = None,
        deadline_seconds: float = 30.0,
    ) -> dict[str, object]:
        started = self.clock()
        attempts = 0
        code = "FAILED"
        try:
            capability = self.registry.resolve(name)
            if not isinstance(payload, Mapping):
                raise IntelError("INVALID_REQUEST", "Expected a mapping")
            if len(payload) > 64 or any(not isinstance(k, str) or len(k) > 64 for k in payload):
                raise IntelError("INVALID_REQUEST", "Invalid input fields")
            if capability.input_keys and set(payload) != capability.input_keys:
                raise IntelError("INVALID_REQUEST", "Input fields do not match contract")
            if isinstance(deadline_seconds, bool) or not isinstance(
                deadline_seconds, (int, float)
            ) or not 0 < deadline_seconds <= 300:
                raise IntelError("INVALID_REQUEST", "Invalid execution deadline")
            # Policy is decided only from host-supplied grants, not payload/model content.
            (authorization or Authorization()).require(capability.permissions)
            # Keep execution bounded before invoking a handler.
            for attempt in range(capability.max_attempts):
                if self.clock() - started >= deadline_seconds:
                    raise IntelError("DEADLINE_EXCEEDED", "Execution deadline exceeded")
                attempts = attempt + 1
                try:
                    result = capability.handler(copy.deepcopy(dict(payload)))
                    if not isinstance(result, (str, dict, list, int, float, bool, type(None))):
                        raise IntelError("VALIDATION_FAILED", "Unsupported output type")
                    import json
                    try:
                        serialized = json.dumps(result, allow_nan=False)
                    except (ValueError, TypeError, RecursionError):
                        raise IntelError("VALIDATION_FAILED", "Output is not valid JSON") from None
                    if len(serialized) > capability.max_output_chars:
                        raise IntelError("VALIDATION_FAILED", "Output exceeds size limit")
                    code = "SUCCEEDED"
                    return {"ok": True, "capability": capability.name,
                            "attempts": attempts, "output": result,
                            "verified": False}
                except RetryableFailure:
                    if attempt + 1 >= capability.max_attempts:
                        raise IntelError("RETRY_EXHAUSTED", "Retryable handler failed") from None
                    delay = min(0.1 * (2 ** attempt), 1.0)
                    if self.clock() - started + delay >= deadline_seconds:
                        raise IntelError("DEADLINE_EXCEEDED", "Retry deadline exceeded") from None
                    self.sleeper(delay)
                except IntelError:
                    raise
                except Exception:
                    raise IntelError("HANDLER_FAILED", "Capability handler failed") from None
            raise IntelError("RETRY_EXHAUSTED", "Retry budget exhausted")
        except IntelError as exc:
            code = exc.code
            return exc.as_result()
        finally:
            self._emit({"event": "agent_capability_completed",
                        "capability": name if isinstance(name, str) and _NAME.fullmatch(name) else "<invalid>",
                        "outcome": code, "attempts": attempts,
                        "elapsed_ms": max(0, round((self.clock() - started) * 1000))})
