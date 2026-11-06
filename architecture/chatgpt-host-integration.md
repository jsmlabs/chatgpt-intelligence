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

**Observed in development on 2026-11-06:** A ChatGPT client successfully
discovered the six G1.9 tools and directly invoked all three
`submit_*_draft` tools over the private tunnel. All three returned
`state: reviewed` and `structural_validation: passed` with
`model_provider: not-attested`. This was an actual live client-mediated
handoff, not a synthetic local-only test. The MCP protocol does not attest
which model authored the submitted text. Structural review does not
constitute human approval or source verification.

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

## G1.9 technical live acceptance evidence (2026-11-06)

**Evidence source:** Direct client tool results observed in the operator's
ChatGPT development conversation. This report does not expose private tunnel
credentials and is not an independent audit of the infrastructure.

| Tool | Observed artifact ID | State | Structural validation |
| --- | --- | --- | --- |
| `submit_prompt_draft` | `d704f3255ef741b48ce9f852ec1bef5e` | reviewed | passed |
| `submit_concept_draft` | `eb504d5133df4f699660fec8b08705a6` | reviewed | passed |
| `submit_document_draft` | `a4f8b329f0bd4cd3a8d02492b545eaf2` | reviewed | passed |

The client advertised six G1.9 MCP tools. The operator also supplied
local PowerShell health evidence: `/healthz` and `/readyz` both returned
HTTP 200 with expected body values. The three client submissions reported
`client_submission: received`, `model_provider: not-attested`,
`llm_generation: not_attested`, `source_verification: not_run`, and
`human_review: not_run`. The source repository revision before G2.1 was
`43faa494a4f35df5a09a3d3080d411bcadd31499` for the original
handoff implementation; the launcher subsequently advanced the repository.
This is **technical handoff acceptance**, not independent model attestation,
an image-rendering adapter, or production-release certification.

### Remaining independent checks

- Independently audit private tunnel permissions and process-wide CREATE scope.
- Verify content quality, source claims and privacy with appropriate review.
- Repeat a fresh-chat or reproducible operator client acceptance test with
  recorded connection/version evidence if required for release.
- Preserve the four existing strict release-readiness blockers.
- `ProviderRouter(chatgpt_host=...)` callback remains an unverified separate
  model-host interface, not established by MCP client submissions.

## G2.1 tool refresh

After pulling the G2.1 commit, restart the local tunnel-client to load the
updated Python MCP process. In the installed ChatGPT Intelligence plugin
settings, use **Refresh tools**. The G2.1 MCP tools
`generate_image_brief` and `submit_image_brief` bring the total to eight.
They return Markdown production briefs and never claim an actual image file.
See [G2.1 IMAGE specification](image-generator.md).
