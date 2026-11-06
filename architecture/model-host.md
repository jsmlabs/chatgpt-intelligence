---
title: G1.6 Opt-in Model Host Integration
status: accepted
classification: experimental
version: 0.2.0
updated: 2026-11-06
---

# G1.6 model integration boundary

**Implemented:** An optional OpenAI Responses API adapter using the Python standard library and an injected host protocol for `PROMPT`, `CONCEPT`, and `DOCUMENT`. It uses the existing `TextRuntime`, `Coordinator` validation and `ArtifactManifest` state graph without changing G0 contracts.

**Not verified:** No authenticated live Responses request or installed native ChatGPT slash-command integration has been exercised as part of this repository work. Mocked HTTP responses only validate the transport contract. Model availability is **not claimed** without an actual configured, authorized call. Nothing connects automatically to the ChatGPT session model.

## Setup

An API key with access to the chosen model is required independently of any ChatGPT subscription. On a trusted local machine, provide `OPENAI_API_KEY` and `INTEL_OPENAI_MODEL` using your operating system's secure environment or secret storage. Do not put credentials in the repository or CLI arguments. Never run a billable model operation merely to test discovery.

```bash
python -m generators prompt --objective "Draft a secure code review prompt" --mode model --authorize-create --authorize-external --authorize-billable
```

The CLI invokes `https://api.openai.com/v1/responses` only when all three permissions are granted and configuration is present. The request uses `store: false`, `max_output_tokens: 2048`, a 20-second timeout and one attempt. HTTP redirects are denied. Content and errors are bounded; provider exceptions and response bodies are never echoed. The adapter is **not** a general-purpose web client. Available output format is Markdown only.

For local no-network generation, omit `--mode model`. The deterministic template remains the default. A model failure never silently substitutes template content.

## Embedding in a trusted host

```python
from generators import Authorization, Permission, TextRuntime, OpenAIResponsesHost

runtime = TextRuntime(model_host=OpenAIResponsesHost())
result = runtime.execute(
    "/INTEL GENERATE DOCUMENT",
    request={"objective": "Draft architecture notes", "audience": "Engineers"},
    authorization=Authorization(frozenset({
        Permission.CREATE, Permission.EXTERNAL, Permission.BILLABLE,
    })),
    mode="model",
)
```

The host constructor reads process environment configuration; it does not grant authority. Callers must construct `Authorization` based on independently authenticated user intent, not model output, source documents or prompt content. Model output remains untrusted text and undergoes deterministic Markdown structure/size checks. A model draft reaches `reviewed` only in the sense of **structural validation**, not editorial approval. The runtime appends factual limitations to model output, and records provider/model/response identifier as host-reported provenance. No automatic source retrieval, tool invocation, repo writes, publishing or deployment is allowed.

The existing revision and export gates apply unchanged. File exports remain exclusive, local, Markdown-only and independently verified. No provider citations are trusted solely because the model generated them.

## Verification

```bash
python -m unittest discover -s tests -v
python scripts/check_docs.py --root .
```

The G1.6 tests use a synthetic model and a stub HTTP response: they check exact permission gates, missing host failures, invalid outputs, non-escalation, supported generator types, provenance, revisions, Markdown export, error sanitization and the documented request shape. **Live invocation: NOT RUN** until a user configures authorized credentials. CI does not spend money and never requires an API key.

[Text Runtime](text-runtime.md) | [Commands](../COMMANDS.md) | [Generator Roadmap](../GENERATOR-ROADMAP.md)

## G1.7 hardened limits and error mapping (2026-11-06)

The model host now defaults to `max_output_tokens=4096` and `timeout=60` seconds. Trusted operators can override limits through `--model-max-output-tokens` (128-8192) and `--model-timeout` (1-120 seconds), or constructor arguments. The bounds are enforced before model execution. No automatic retries or model/provider substitution were introduced.

Safe, stable error codes include `MODEL_OUTPUT_INCOMPLETE` for incomplete Responses statuses (including `max_output_tokens` exhaustion), `MODEL_TIMEOUT`, `MODEL_AUTH_FAILED`, `MODEL_QUOTA_EXHAUSTED`, `MODEL_RATE_LIMITED`, `MODEL_REQUEST_REJECTED` and `MODEL_PROVIDER_UNAVAILABLE`. Unrecognized cases remain `MODEL_REQUEST_FAILED`. The HTTP 429 code is determined only from an at-most-8-KiB provider-error payload and no raw response body is exposed. A model returning `incomplete` is **not** counted as successful generation.

An operator independently reported a three-generator live smoke run on the preceding revision with `PASSED` for PROMPT, CONCEPT and DOCUMENT. This is user-supplied external evidence, **not** CI evidence and **not** verification of the hardened commit. The new exact revision requires its own live test. Neither smoke result proves ChatGPT client installation or factual accuracy.
