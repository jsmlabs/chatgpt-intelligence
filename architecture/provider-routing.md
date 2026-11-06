---
title: G1.8 Zero-Paid-Default Provider Routing
status: accepted
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

## G1.8.1 Markdown normalization

Model-generated Markdown may begin with prose or be wrapped in one full Markdown
fence. The local runtime removes the single enclosing Markdown fence, inserts
a missing generator-specific H1, and appends a provenance section using actual
line breaks. Existing size, NUL and structural checks remain mandatory.
No retries or fallback requests are added. This normalization is deterministic;
source verification and human review remain separate.

## G1.8.2 - Fenced Markdown validation

A user-reported live Ollama `CONCEPT` result on revision
`7a93a81ad5ebbea007f5f5c00c94399f33c0abcf` returned a valid local
concept and structural validation `passed`, but contained an **unclosed outer
Markdown code fence**. The earlier validator did not detect the formatting defect.

Now, the runtime unwraps a clearly delimited outer Markdown fence, and repairs
an otherwise-unambiguous lone opening `markdown` fence at the beginning.
Nested/ambiguous and unbalanced code fences fail structural validation rather
than consuming the provenance section. Ordinary balanced code examples remain
unchanged. No second model call, network action, or billable fallback is triggered.

Evidence: user-provided PowerShell transcript in the project conversation,
not independently retrieved machine logs. This is evidence for the earlier
local `CONCEPT` generator only, not for G1.8.2 on the user's machine.
`PROMPT` and `DOCUMENT` local live execution remain outstanding.

## Local PROMPT/DOCUMENT smoke test

Run from the repository root on a machine with a running Ollama daemon
and a downloaded model. This verifier **never uses** the OpenAI API:

```powershell
$env:INTEL_OLLAMA_MODEL = "gemma3:4b"
python -m scripts.verify_ollama_live --authorize-local-inference
```

The opt-in verifier checks Ollama reachability, runs one local inference for
each of `PROMPT` and `DOCUMENT`, and reports provider, artifact state,
structural validity, fence balance, and independent review flags. No raw
model-generated text is printed, and no outcome is marked passed until
the verifier actually runs. Optional `--types` includes `CONCEPT`.
