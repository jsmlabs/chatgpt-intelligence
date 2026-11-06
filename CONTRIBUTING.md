# Contributing

We aim for explanations anyone can follow, without sacrificing technical accuracy.

## Before editing
1. Check whether the topic already has a canonical home.
2. Explain the subject plainly before introducing jargon.
3. Separate **officially documented behavior**, **observed behavior**, **inference**, and **proposal**.
4. Cite sources and verification dates for changeable product claims.
5. Use realistic but synthetic examples; do not publish private chat histories or personal memory data.

## Naming and structure
- Use English and descriptive `kebab-case.md` filenames.
- Use relative links between documents.
- Keep one primary owner per concept; link instead of copying material.
- Add directories only when they have useful content.
- Use the [document template](templates/document-template.md) when it helps. Do not add empty headings mechanically.

## Suggested status labels
`draft` (work in progress), `proposed` (ready for discussion), `accepted` (project design approved), `deprecated` (superseded). These labels do **not** prove that a ChatGPT capability exists.

## Review checklist
- Is the purpose clear in the opening paragraph?
- Would a first-time reader understand the terminology?
- Are factual claims appropriately sourced and dated?
- Are limitations and trade-offs explicit?
- Do examples and links work?
- Is this the simplest useful structure?


## G0 implementation guidance

- Python 3.11 standard library only for the G0 reference package.
- Keep validation, authorization, availability checks and execution distinct; do not derive permissions from models, source text or command flags.
- New generators register with `generators.foundation.Registry`; mark `AVAILABLE` only after implementing and verifying the host adapter.
- Use synthetic tests in `tests/test_generators.py`. A mock passing is not evidence that any external tool is operational.
- Do not introduce provider endpoints, publishing, API keys or generated artifacts during G0.
- [Runtime contract](architecture/generator-foundation.md) and [roadmap](GENERATOR-ROADMAP.md) are the sources of truth.

## G1 developer workflow

For text-generation changes, extend [the local runtime](architecture/text-runtime.md) and add cases to [G1 tests](tests/test_text_runtime.py). Preserve the G0 `Coordinator` contract, do not treat untrusted user content as authorization, and distinguish structural validation from human review or model verification. Check the exact commit in GitHub Actions before claiming CI passed. Do not add model providers without a verified host adapter and explicit side-effect permissions.

## Model-backed integration boundary

Keep model transport in `generators/model_host.py` and deterministic authorization in the runtime. Any new provider must be independently authenticated and preserve explicit external/billable permission checks, size/time budgets, error sanitization and output validation. Synthetic provider tests must not be described as live integration evidence. No credentials in commits or test fixtures.

## MCP host verification

Do not claim live-model or ChatGPT client support from synthetic MCP unit tests. A live call uses `-m scripts.verify_model_live --authorize-live-billable` only with credentials provisioned outside source control and with explicit operator authorization. Keep the MCP stdio transport free of additional filesystem, network retrieval or publishing tools unless separately designed and approved. See [MCP host](architecture/mcp-host.md).
## G1.7 model-budget hardening

When tuning the model transport, keep bounded limits and explicit host-operator configuration, never retry billable requests silently. Unit-test rejected `incomplete` responses, transport timeouts, and HTTP 429 quota/rate-limit distinctions with synthetic payloads. User-provided prior live outcomes do not automatically certify a newer commit.

## G1.8 provider rules

Preserve offline default behavior and billable provider opt-in. Local Ollama is loopback-only with an explicitly selected installed model; no automatic download or cloud fallback. `chatgpt-host` requires a trusted injected adapter and verified tool declaration. Test providers with synthetic data and no live/paid CI requests.
