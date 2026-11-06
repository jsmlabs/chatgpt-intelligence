---
title: G1 Text-first MVP Runtime
status: accepted
classification: experimental
version: 0.2.0
updated: 2026-11-06
---

# G1: Local text-first MVP

**Implemented:** Three deterministic Markdown renderers (`PROMPT`, `CONCEPT`, `DOCUMENT`), typed request validation, permission gate, a shared artifact lifecycle, revision lineage and verified local Markdown export. **Not implemented:** native ChatGPT integration, model-backed writing, source retrieval, PDF/DOCX export, hosted persistence, publishing or deployment. The remaining 13 registered generator types are planned.

## Supported execution

Use Python 3.11+ from the repository root; no third-party dependencies:

```bash
python -m generators prompt --objective "Review a Python API" --audience "Engineers" --authorize-create
python -m generators concept --objective "Compare onboarding flows" --authorize-create
python -m generators document --objective "Write a deployment runbook" --authorize-create
```

These commands print editable Markdown to stdout and a machine-readable summary to stderr. Their output is **template-produced**, not AI-generated or fact-checked. The CLI `--authorize-create` grants local artifact creation to the CLI process only. The text of the objective and sources never grants authority. No files are written unless both `--export-root` and `--filename` are supplied:

```bash
mkdir -p artifacts
python -m generators document --objective "Document a local API" --authorize-create --export-root artifacts --filename api.md
```

Export creates a new `.md` file exclusively, rejects paths outside the chosen existing root, rejects symlink traversal, reads back bytes and validates their SHA-256 digest. It will not overwrite an existing path. Avoid directories writable by untrusted concurrent actors; OS-level sandboxing and race-free host-level storage controls remain the integrating application's responsibility.

## Python host API

```python
from generators import Authorization, Permission
from generators.text_runtime import TextRuntime

runtime = TextRuntime()
result = runtime.execute(
    "/INTEL GENERATE PROMPT",
    request={"objective": "Review a Python API", "audience": "Developers"},
    authorization=Authorization(frozenset({Permission.CREATE})),
)
assert result["ok"]
assert result["manifest"].state.value == "reviewed"
```

`TextRuntime` validates the brief before calling the G0 `Coordinator`. It activates only three local renderer adapters and never advertises unsupported providers. `Coordinator` and `default_registry` from G0 remain unchanged for callers that depend on the G0 behavior. The tool resolver is still deny-by-default for external capabilities.

## Lifecycle and evidence

`planned -> ready -> generating -> validating -> reviewed` for structural Markdown validation. Optional verified local export moves to `exported`. Failures transition to `failed`; requests denied before allocation produce no manifest. `reviewed` means **automated structure checked**, not a human editorial review. Returned evidence explicitly marks `human_review`, `source_verification` and `llm_generation` as `not_run`. All external references are user-declared and unverified.

Revision uses `TextRuntime.execute(..., previous=prior_manifest)`. Only previously reviewed or exported manifests can be revised. Each revision has a distinct identifier, new version and parent link; the original is never modified.

## Acceptance tests

Run `python -m unittest discover -s tests -v`. Targeted tests cover nine golden cases (three per generator), missing inputs, malicious-looking source text, permission denials, unsupported output formats, collision and symlink guards, file existence/byte-integrity checks, and lineage. No tests claim an external model or ChatGPT host works.

**Limitations:** Templates are reusable drafts rather than full creative reasoning. Production model adapters, source verification, human review and client-side UX require separate implementation and authorization. The original seven knowledge domains remain untouched.

[Roadmap](../GENERATOR-ROADMAP.md) | [Commands](../COMMANDS.md) | [G0 boundaries](generator-foundation.md)
