# AI agent capability runtime

Status: implemented (offline orchestration boundary). This module does not provide an autonomous model agent, remote tool discovery, persistence, or a security sandbox.

## Purpose and contract

`generators.agent_runtime` provides a narrow, dependency-free extension point for host-supplied AI-agent capabilities. The implementation is deliberately isolated from `ProviderRouter` and the existing generator registry; importing it cannot enable providers or change existing CLI behavior.

- **Capability routing:** Host code registers named `AgentCapability` handlers in `AgentRegistry`. Unknown names fail closed. There is no dynamic import, arbitrary shell execution, or model-authored registration.
- **Permission gates:** A registered capability declares a fixed `frozenset[Permission]`. The caller supplies `Authorization`; input payloads and model output cannot grant privileges. The gate runs before the handler, including before every retry.
- **Retry strategy:** A handler must explicitly raise `RetryableFailure`; only registered `idempotent=True` capabilities may set `max_attempts` above one (hard maximum three). Backoff is 100/200 ms, bounded by the caller's deadline. No automatic retries on arbitrary exceptions, authorization errors or output validation failures.
- **Observability:** An injected observer receives one `agent_capability_completed` event with capability identifier, outcome code, attempt count and elapsed milliseconds. Inputs, outputs, exception details, credentials and grants are not included. Observer exceptions do not affect the result.
- **Output boundary:** Results must be JSON-serializable, finite and smaller than the per-capability size cap. All outputs remain **unverified** unless independently validated by a domain-specific consumer.
- **Timing:** The deadline is cooperative and checked before handler calls and retries. It does **not** interrupt an already running blocking handler. Hosts must provide transport-level timeouts and cancellation.
- **Reliability:** Successful execution is not a durable checkpoint or exactly-once guarantee. Idempotency must be truthful and enforced by each handler or downstream service.

## Minimal example

```python
from generators.agent_runtime import AgentCapability, AgentRegistry, AgentRuntime
from generators.foundation import Authorization, Permission

def summarize(request: dict[str, object]) -> dict[str, object]:
    # Replace with an injected, explicitly configured adapter.
    return {"summary": str(request["text"])[:100]}

registry = AgentRegistry((
    AgentCapability(
        name="text.summarize",
        handler=summarize,
        permissions=frozenset({Permission.CREATE}),
        input_keys=frozenset({"text"}),
        idempotent=True,
        max_attempts=2,
    ),
))
events = []
runtime = AgentRuntime(registry, observer=events.append)
result = runtime.execute(
    "text.summarize",
    {"text": "A synthetic example"},
    authorization=Authorization(frozenset({Permission.CREATE})),
)
assert result["ok"]
```

## Integration guidance

Register only trusted handler functions. Keep model prompts/results untrusted, define JSON schemas at each adapter boundary, validate requested operations against server-side policy, and use transport-level request timeouts. Side-effecting tools should generally be non-retryable unless a durable downstream idempotency key is enforced. Before adding a live or billable provider, reuse the existing provider-specific authorization and tool-verification contracts; this module grants no provider access.

## Verification

Run `python -m unittest tests.test_agent_runtime -v` or the repository's full `python -m unittest discover -s tests -v`. These tests use synthetic local handlers and do not exercise an external model, production credentials, network or a live deployment.

See [generator foundation](generator-foundation.md), [provider routing](provider-routing.md), and [Forge Studio integration](../integrations/forge-studio.md).
