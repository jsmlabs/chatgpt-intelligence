---
title: G1.7 Local MCP Host and Live Verification
status: accepted
version: 0.3.0
updated: 2026-11-06
classification: experimental
---

# G1.7 - MCP stdio host

Implemented: a local, dependency-free MCP stdio JSON-RPC server offering three tools: `generate_prompt`, `generate_concept` and `generate_document`. It invokes the existing `TextRuntime` and does not change G0 permission or artifact contracts. The supported handshake protocols are `2025-06-18` and `2025-11-25`. This is an executable **local host surface**, not an installed ChatGPT plugin or public MCP endpoint.

## Start and configure

A compatible MCP client may launch the process with the working directory set to the project root:

```bash
python -m generators.mcp_server --allow-create
```

The process uses stdin/stdout as its JSON-RPC transport. No HTTP listener, file-export tool, repository write tool or arbitrary command execution capability is exposed. Any server logs must go to stderr; stdout is reserved for protocol frames.

**Operator permissions:** Without flags the server advertises its tools but denies all creation calls. `--allow-create` enables local Markdown draft creation in memory, not filesystem writes. `--allow-external` and `--allow-billable` must be explicitly added to permit model mode. Never copy model-authentication secrets into client configuration text, tool arguments or repository files. Treat clients with permission to call this process as trusted operators; these startup flags grant permissions for the lifetime of the local process, not per-user identity. For shared/multi-user production, implement authenticated per-request grants instead.

To allow explicitly billable model calls with a separately provisioned environment:

```bash
python -m generators.mcp_server --allow-create --allow-external --allow-billable
```

The tool argument `mode` defaults to `template`, which makes no network requests. `mode=model` requires the additional startup grants AND valid `OPENAI_API_KEY` and `INTEL_OPENAI_MODEL` environment configuration. No credential is required to list tools or use local template mode. No tool arguments can grant authority or override the model host selection.

## Live provider smoke test

Before claiming any model API integration is operational, explicitly provision API access **outside GitHub**. From a trusted terminal, with `OPENAI_API_KEY` and `INTEL_OPENAI_MODEL` present:

```bash
python -m scripts.verify_model_live --authorize-live-billable
```

This invokes one potentially billable Responses API request for each of the three generator types, stops on the first failed call and reports only status, output validation and provider response-ID presence. Raw API keys and generated content are never printed. The underlying host sets `store: false`, a request timeout and output size/token budgets. **GitHub CI does not run this script**. Absence of configuration results in `BLOCKED`, not a simulated pass.

## Client integration status

The local MCP stdio server is compatible with host applications that support launching local commands over stdio. Connecting this to ChatGPT requires an actually supported client/plugin transport and a user-authorized installation. ChatGPT availability cannot be inferred from local MCP passing tests, and this repository does not expose an authenticated remote service.

## Security and limits

- The G0 `Authorization` instance is created once from trusted startup flags; generated text and tool inputs cannot add permissions.
- MCP calls have a 32-KiB incoming-line limit, bounded request fields, and sanitized JSON-RPC errors.
- The three tools only return in-memory Markdown drafts plus manifests; no arbitrary source retrieval, publishing, file writes or client-provided URLs are executed.
- `reviewed` means structural validation, **not human review**. Model provenance is host-reported, not independently audited.
- The live provider smoke test is separate from synthetic MCP/transport unit tests. Server authentication and production-grade shared-host isolation are not implemented.

## Acceptance

```bash
python -m unittest discover -s tests -v
python scripts/check_docs.py --root .
```

Expected CI verification: protocol handshake, tool discovery, real local stdio subprocess, deny-by-default, authorized template mode, synthetic model mode, malformed requests and oversized input. These are contract tests, not proof of live API success or an installed ChatGPT plugin.

[Commands](../COMMANDS.md) | [Model host](model-host.md) | [Text runtime](text-runtime.md)
