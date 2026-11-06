---
title: Forge Studio interoperability
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# Forge Studio integration

ChatGPT Intelligence and [Forge Studio](https://chatgpt.com/plugins/Plugin_073c7872c6a4819184b4ee75669ab6ac) are independently versioned products. Forge Studio 3.3.0 provides an opt-in, bounded local MCP stdio bridge and a separately authorized, deterministic workflow engine for orchestrating supported Intelligence tools. An existing ChatGPT Intelligence connector is an independent host integration.

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

## Forge Studio v3.2 - published reliability upgrade

**Status (2026-11-06):** Forge Studio 3.2.0 is published and verified by plugin-release read-back. The existing 29 skill identities and four CLI entrypoints remain stable; the MCP client adds `--require-tool` as a backwards-compatible option.

The improved bridge sends `notifications/initialized` before discovery, validates protocol IDs and the declared host identity, enforces bounded JSON frames, rejects duplicate/invalid tool inventories, and reports structured timeout, transport and capability failures. The local child process still requires explicit `--execute`, forwards only the `--allow-create` grant, and remains **not a sandbox**.

**Verification evidence:**

- Forge Studio: 58/58 local Python tests passed both in the working distribution and independently after extracting the release ZIP; CLI compatibility and structural release checks passed.
- GitHub Intelligence: [Documentation Quality run 42291594097](https://github.com/jsmlabs/chatgpt-intelligence/actions/runs/42291594097) completed successfully at commit `954410e9c70ee0af7e68b0287f69876815ab4699`, including the complete repository unittest suite, documentation, privacy scan and media checks.
- Real Intelligence host: `tests/test_forge_interop.py` exercises a genuine local MCP process with handshake, discovery, an offline template artifact and a denied billable mode, as part of repository CI.
- ChatGPT client: a connected `ChatGPT_Intelligence.generate_prompt` tool call succeeded in the integration conversation with `structural_validation: passed`. This confirms that individual connector call, not permanent tunnel availability or model-provenance attestation.
- Plugin platform: current release `3.2.0`, 29 skills and revised CLI contract were read back after publication.

**Remaining independent acceptance:** Forge Studio's own CLI has not been executed against a complete real Intelligence checkout inside the user's local operating system. No automatic remote installation, continuous service connectivity, unrestricted local code isolation or production security certification is claimed. Local operator acceptance can use:

```sh
python scripts/forge_intelligence.py /trusted/chatgpt-intelligence --execute --require-tool generate_prompt --tool generate_prompt --arguments '{"objective":"Offline local acceptance","provider":"template"}'
```

See the published [Forge Studio plugin](https://chatgpt.com/plugins/Plugin_073c7872c6a4819184b4ee75669ab6ac) and its `references/bridge-reliability.md` for the detailed contract.

## Forge Studio v3.3 - Unified Workflow Engine

**Published and verified on 2026-11-06:** Forge Studio v3.3.0 is an additive release with 30 skills and five CLI entrypoints; the original Intelligence MCP host and permission model are unchanged. Release metadata and the workflow source, skill, contract and tests were read back from the Plugin Creator after publication.

The workflow engine is intentionally narrow: a JSON schema-v1 contract with 1-32 ordered steps and a fixed action registry. It supports `core.echo`, `core.sha256`, and offline Intelligence `generate_prompt`, `generate_concept` and `generate_document` actions. Each external action checks the existing MCP bridge allowlist and actual discovery. Workflow-supplied content cannot create new actions or authorize them.

- **Deterministic state:** `planned`, `running`, `succeeded`, `failed`, `blocked`, and `uncertain`. Dependencies must refer to earlier steps; model results never determine permissions.
- **Durable checkpoints:** SQLite records the canonical workflow hash, run key, attempts and step outcomes. Reusing a run key for a different workflow is rejected.
- **Idempotency and recovery:** successful steps do not re-execute for a given run key; a process-interrupted or failed external call is marked `uncertain` and is never blindly retried. Explicit `--retry-failed` only permits known deterministic local failures.
- **Permission boundaries:** planning performs no execution or checkpoint writes; execution requires `--execute`, and Intelligence generation additionally requires a caller-granted `--grant create`. No arbitrary shell, deployment, paid model, or unrestricted ChatGPT connector proxy is installed.
- **Verification:** 74/74 Forge Studio Python tests passed in the source package and independently after extracting the release ZIP. The five-CLI compatibility gate and the structural release gate passed, including 53 required files. This verifies the packaged runner and synthetic MCP adapter boundary, **not** an operator Windows deployment or distributed exactly-once execution.

### Workflow sample

Create `workflow.json` in an appropriate trusted working directory:

```json
{"schema":1,"name":"draft-and-digest","steps":[{"id":"draft","action":"intelligence.generate_prompt","input":"Design a narrow API contract"},{"id":"digest","action":"core.sha256","depends_on":["draft"],"from_step":"draft"}]}
```

With a complete trusted Forge Studio plugin checkout and Intelligence checkout, run:

```sh
python scripts/forge_workflow.py plan --workflow workflow.json --db state.sqlite --run-key sample
python scripts/forge_workflow.py run --workflow workflow.json --db state.sqlite --run-key sample --execute --grant create --intelligence-root /trusted/chatgpt-intelligence
python scripts/forge_workflow.py status --db state.sqlite --run-key sample
```

The `state.sqlite` checkpoint must live outside the plugin installation. A subprocess is **not** an isolation sandbox. Real cross-project execution on the operator's Windows machine and live ChatGPT host activation remain independent acceptance steps.

## Forge Studio v3.3.1 - operator-local acceptance

**Published:** Forge Studio v3.3.1 adds the optional `scripts/forge_acceptance.py` CLI. It is additive to the v3.3 workflow engine and does not change ChatGPT Intelligence's MCP host or permissions.

The command accepts an explicit trusted local Intelligence checkout and defaults to a read-only plan. With `--execute`, it launches the existing Forge workflow engine and local MCP bridge, calls offline `generate_prompt`, hashes the returned draft, resumes the same SQLite run and checks both step attempt counts are exactly one. It creates ephemeral state and returns bounded JSON status and error codes; no persistent checkout mutation is intended.

```powershell
python scripts/forge_acceptance.py C:\\projects\\chatgpt-intelligence
python scripts/forge_acceptance.py C:\\projects\\chatgpt-intelligence --execute
```

**Verification:** All 79 Forge Studio unit tests passed when run by test module, including five new acceptance tests using a synthetic local MCP subprocess. The six-CLI compatibility gate and structural release gate passed on the source and independently extracted release ZIP; 55 required files were checked. Plugin Creator release 3.3.1 was published and read-back verification is tracked separately. A synthetic host does **not** establish a live run against the user's Windows checkout. The process is **not a security sandbox** and SQLite idempotency is **not distributed exactly-once execution**.

**Operator acceptance remains required:** Run the command against the actual Windows checkout and verify its Git SHA and exit status. Keep the real host's own tests and CI evidence separate from Forge's local tests.
