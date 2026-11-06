---
title: G1.8 Zero-Paid-Default Provider Routing
status: implemented
version: 0.4.0
updated: 2026-11-06
---

# G1.8 - Offline-first routing

The local CLI and stdio MCP server default to deterministic `template` execution, requiring neither an API key nor external network access. The 16-entry registry and artifact lifecycle remain unchanged.

| Provider | Runtime | Grants | Evidence boundary |
| --- | --- | --- | --- |
| `template` | Deterministic Markdown | CREATE | Built in, offline |
| `ollama-local` | Fixed loopback `127.0.0.1:11434` | CREATE + EXTERNAL | Read-only `/api/tags` installed-model probe, followed by explicit generation |
| `chatgpt-host` | Injected host callback | CREATE | Requires injected adapter and verified/reachable ToolDeclaration; standalone CLI/MCP cannot access native ChatGPT |
| `openai-api` | Optional Responses API | CREATE + EXTERNAL + BILLABLE | Valid credentials and available API balance required |

The model runtime is **selected by a trusted caller**, not by untrusted brief text. `ProviderRouter.detect()` reports passive configuration, grants and verification evidence without any network call; no claimed connected ChatGPT tool is fabricated. There is no automatic fallback to cloud, model download, retry, or silent paid invocation.

## Commands

```bash
python -m generators prompt --objective "Draft a checklist" --authorize-create
```

Optional locally installed Ollama: install Ollama separately, pull a model explicitly and set the matching environment variable. A model download consumes bandwidth and disk space, but inference requires no paid cloud API subscription:

```bash
ollama pull gemma3:4b
export INTEL_OLLAMA_MODEL=gemma3:4b
python -m generators concept --objective "Design a dashboard" --provider ollama-local --authorize-create --authorize-external
```

Optional paid provider (never implicit):

```bash
python -m generators document --objective "Draft docs" --provider openai-api --authorize-create --authorize-external --authorize-billable
```

For backwards compatibility, `--mode model` still means explicitly selected `openai-api` and still requires the external and billable grants. `--mode template` remains the default. A conflicting combination of `--mode model` and a non-API provider fails closed.

The MCP tool arguments also accept `provider`. A host that actually exposes a ChatGPT model may inject `ProviderRouter(chatgpt_host=adapter, host_tools=ToolResolver(...))` with a verified `chatgpt-host` declaration. This does **not** install or imply a native ChatGPT plugin.

## Verification

CI uses synthetic providers and mocked loopback HTTP only. A genuine installed Ollama model and a native ChatGPT connection are separate end-to-end verification gates. Model-generated drafts are structurally reviewed, not human-reviewed or source-verified.
