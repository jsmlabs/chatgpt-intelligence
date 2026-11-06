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
