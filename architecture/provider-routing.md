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
`PROMPT` and `DOCUMENT` were subsequently executed successfully on G1.8.2, as recorded below.

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

## User-reported Ollama live acceptance (2026-11-06)

Source of evidence: Windows PowerShell 5.1 terminal transcript supplied by the
operator in the project conversation. This is **user-reported live evidence**,
not provider logs independently retrieved by the repository maintainers.

- Repository revision: `f5a9b67341e2a7e2b6e72c3d2768f5c29508799e` (operator ran `git rev-parse HEAD`).
- Ollama model: `gemma3:4b` (operator configured `INTEL_OLLAMA_MODEL`).
- Invocation: `python -m scripts.verify_ollama_live --authorize-local-inference --model-timeout 120 --model-max-output-tokens 4096`.
- Report-level status: `PASSED`, `local_model_attempted: true`.
- `PROMPT`: `PASSED`, provider `ollama-local`, state `reviewed`, `structurally_valid: true`, `balanced_code_fences: true`.
- `DOCUMENT`: `PASSED`, provider `ollama-local`, state `reviewed`, `structurally_valid: true`, `balanced_code_fences: true`.
- Both: `human_reviewed: false` and `source_verified: false`.
- `CONCEPT`: earlier user-reported local live pass was on revision `7a93a81ad5ebbea007f5f5c00c94399f33c0abcf`, **not** the current G1.8.2 revision; the earlier output exposed an outer code-fence formatting issue that G1.8.2 addresses.

**Acceptance scope:** Local `PROMPT` and `DOCUMENT` inference on G1.8.2 is
user-reported as passed. A full three-generator live smoke test on a *single*
G1.8.2 revision, independent content review and actual ChatGPT-host connection
remain unverified. No separate OpenAI API call or billable grant was needed
for the reported Ollama verifier.

## Full three-generator local live acceptance (2026-11-06)

The operator supplied another Windows PowerShell 5.1 terminal transcript after
a fast-forward pull from `f5a9b67` to
`94eb43de04a3ef8c0807afaf0889587567ac0bdd`. The transcript reports:

```powershell
$env:INTEL_OLLAMA_MODEL = "gemma3:4b"
python -m scripts.verify_ollama_live --authorize-local-inference --types PROMPT CONCEPT DOCUMENT --model-timeout 120 --model-max-output-tokens 4096
```

- Report-level `status: PASSED`, `local_model_attempted: true`.
- `PROMPT`, `CONCEPT` and `DOCUMENT`: each `status: PASSED`,
  `provider: ollama-local`, `state: reviewed`,
  `structurally_valid: true`, `balanced_code_fences: true`.
- All three: `human_reviewed: false`, `source_verified: false`.

**Evidence classification:** User-reported local end-to-end output, not an
independently accessed host log. This supersedes the earlier open full-suite
G1.8.2 live-acceptance item. No billable API grant was used by this verifier.
A native ChatGPT-host integration, independent content review and the
repository's existing release gates remain outstanding.
