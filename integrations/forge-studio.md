---
title: Forge Studio interoperability
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# Forge Studio integration

ChatGPT Intelligence and [Forge Studio](https://chatgpt.com/plugins/Plugin_073c7872c6a4819184b4ee75669ab6ac) are independently versioned products. Forge Studio 3.1.0 provides an opt-in, bounded local MCP stdio bridge to the Intelligence generator host, plus a documented workflow for invoking an existing ChatGPT Intelligence connector.

## Ownership and integration boundary

- **Intelligence owns** deterministic generators, generator schemas, stdio MCP host, artifact creation permission, and optional provider authorization.
- **Forge Studio owns** engineering review, implementation workflows, local opt-in check runner, security/quality assessment, and its bridge client.
- **ChatGPT host owns** installed connector discovery, invocation permissions and client visibility. A GitHub source tree is not evidence that a specific tool is connected in ChatGPT.
- Neither side imports arbitrary tools or treats model-generated content as permission. No automatic token sharing, remote server exposure or unlimited code execution.

## Local usage

From an installed, trusted complete Forge Studio package, with a trusted checkout of this repository:

```sh
# No subprocess by default
python scripts/forge_intelligence.py /path/to/chatgpt-intelligence

# Explicit local MCP subprocess handshake and tool discovery
python scripts/forge_intelligence.py /path/to/chatgpt-intelligence --execute

# Offline deterministic prompt generation
python scripts/forge_intelligence.py /path/to/chatgpt-intelligence --execute --tool generate_prompt --arguments '{"objective":"Describe a safe API","provider":"template"}'
```

The bridge starts `python -m generators.mcp_server --allow-create`, checks the server-advertised tool names against a fixed allowlist, validates bounded JSON messages and uses a process deadline. It does not pass external/billable provider permissions or ComfyUI flags. The local subprocess is **not a security sandbox**; explicit execution must be limited to trusted code.

## Connected ChatGPT usage

When both integrations are independently available in the same chat, call only tools actually advertised by the ChatGPT Intelligence connector. For example, `generate_prompt`, `generate_concept`, `generate_document` and their `submit_*_draft` handoff forms may be present. Capture the actual returned validation state and provenance; then use Forge Studio engineering skills to inspect, implement, test and document downstream changes. Do not treat an in-memory draft as a verified source, applied code change or deployed artifact.

## Verification and limitations

Forge Studio 3.1.0 ships an MCP bridge and synthetic subprocess protocol tests. These establish client-side behavior but **do not prove** a real local checkout handshake, fresh ChatGPT client connection, tunneled MCP availability, private deployment or full generator coverage. Verification must be repeated for the actual revision and installation. Keep the independent projects' release gates separate.

See [MCP host](../architecture/mcp-host.md), [host integration](../architecture/chatgpt-host-integration.md), and [source resolution](../architecture/activation-and-source-resolution.md).

## Forge Studio v3.2 release candidate - live connectivity and reliability

**Status (2026-11-06):** v3.2 is a locally tested candidate, not a published Forge Studio release. The current published plugin remains v3.1.0 until all release gates pass.

The candidate tightens the existing opt-in MCP client without adding remote, billable, ComfyUI or shell permissions:

- Sends `notifications/initialized` before tool discovery and validates MCP protocol, IDs, server identity and result structure.
- Enforces bounded JSON arguments, frames and inventory; rejects duplicate tool declarations and unavailable tools.
- Adds repeatable `--require-tool` fail-closed discovery checks and stable error codes for transport, protocol, timeout and permission-related failures.
- Limits local subprocess duration to 1-120 seconds; no checkout code runs without `--execute`.
- Keeps the ChatGPT connector path independent from the local stdio path and records evidence tiers distinctly.

**Actual evidence:** The v3.2 Forge Studio candidate passed its local 58-test suite, CLI compatibility and structural package checks. A connected ChatGPT Intelligence `generate_prompt` call returned a structurally validated offline draft, demonstrating that the tool was reachable in the invoking session. This is **not** proof of a Forge CLI subprocess executing the current GitHub checkout. The added `tests/test_forge_interop.py` invokes the real local Intelligence MCP host in GitHub CI with an offline template request and verifies that model mode without external/billable grants is denied.

**Release blocker:** GitHub Actions run [42291154597](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42291154597) failed in the complete regression suite because seven `tests/test_configuration_setup.py` cases failed. The log does not attribute those failures to the new MCP integration test, but a green whole-repository gate is absent. No overall passing CI or v3.2 production certification is claimed.

**Acceptance still required:** Fix and verify the seven configuration-CLI failures without weakening tests, re-run the full workflow on the final revision, execute the Forge CLI against an actual trusted checkout if operator access permits, then publish and read back the Forge Studio release. Preserve both projects' independent authorization and provenance boundaries.
