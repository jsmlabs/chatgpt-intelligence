---
title: G1.9 ChatGPT MCP Client Handoff
status: accepted
version: 0.5.0
updated: 2026-11-06
classification: experimental
---

# G1.9 - ChatGPT-to-INTEL MCP handoff

## Implemented versus unverified

**Implemented:** The stdio MCP server now exposes `submit_prompt_draft`,
`submit_concept_draft` and `submit_document_draft`. A ChatGPT client may
generate Markdown using its own conversation model, then submit that content
through one of these MCP tools. The Python runtime validates the untrusted
draft with G0 creation permissions, Markdown checks, balanced code fences
and the existing artifact state transitions, returning an in-memory
`reviewed` artifact. No model HTTP request, additional OpenAI API billing
or Ollama process is needed for the handoff.

**Not verified:** Whether the current ChatGPT account/workspace can attach
and invoke this local MCP server. The server cannot directly call the ChatGPT
conversation model; the model's authorship of the submitted text is **not
attested**. The resulting provenance is `client-submitted-draft`,
`model_provider: not-attested`, `llm_generation: not_attested`.
Structural review does not constitute human approval or source verification.

The previous `generate_*` tools, template/Ollama/OpenAI routing,
16-entry registry and artifact lifecycle are preserved.

## Local verification (no model needed)

From the repository root on Windows PowerShell 5.1:

```powershell
python -m unittest discover -s tests -v
python -m scripts.verify_host_mcp --authorize-local-create
```

The smoke test launches the real stdio MCP process, performs an initialize
handshake and submits all three synthetic Markdown drafts. Its report has
`chatgpt_client_connected: false` by design and must not be mistaken
for a native ChatGPT live end-to-end test.

## ChatGPT connection - operator prerequisites

Current OpenAI documentation confirms that ChatGPT attaches to remote MCP
endpoints (public HTTPS streamable HTTP or Secure MCP Tunnel), **not directly
to local stdio**. Secure MCP Tunnel supports an existing local stdio command,
so no paid model API or public server is needed.

Official sources:

- [Custom MCP server connection](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)
- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [Plugin connection testing](https://developers.openai.com/plugins/deploy/connect-chatgpt)

Before attempting installation, verify that your account/workspace can add
custom MCP plugins, that a Platform tunnel can be created and associated
with the target ChatGPT workspace, and that the operator has the appropriate
tunnel permissions and runtime credential. This access is **not granted
by having a ChatGPT subscription** and must not be presumed available.

The trusted local stdio command for the tunnel profile is:

```powershell
python -m generators.mcp_server --allow-create
```

Configure the official `tunnel-client` with this command from the project
root, run its `doctor` check, and keep the authenticated tunnel running.
In ChatGPT Plugins, select **Add custom MCP server**, use the Tunnel
connection option and the authorized tunnel ID. Review the declared
tools, warnings and permissions before creating and enabling the plugin.
The client should then write a draft and invoke the corresponding
`submit_*_draft` tool with `objective` and `content`.

Do not enable `--allow-external` or `--allow-billable` for this workflow.
The `--allow-create` grant is process-wide, not per-ChatGPT-user
authorization. Keep the tunnel private, authenticate access, and do not
publish tunnel credentials in source control. The tunnel requires separate
Platform/workspace provisioning; its cost and eligibility must be checked
rather than assumed to be universally free.

## Live acceptance gates - BLOCKED / NOT RUN

1. Actual supported account and workspace connection established.
2. Secure tunnel health and MCP discovery verified.
3. Client discovers three `submit_*_draft` tool schemas.
4. Actual ChatGPT client generates and submits PROMPT, CONCEPT, DOCUMENT.
5. Permission denial, no billing fallback and provenance labels confirmed.
6. Record the exact repository revision and client connection evidence.

Only a real client-driven run can clear these gates. Do not claim that the
`ProviderRouter(chatgpt_host=...)` callback path works without a separate
verified host adapter, or that an MCP submission proves specific model origin.
