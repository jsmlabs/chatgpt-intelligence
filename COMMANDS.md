---
title: ChatGPT Intelligence Command Reference
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# ChatGPT Intelligence - /INTEL

`/INTEL` is a **proposed natural-language activation convention** for using this repository within ChatGPT. It is **not** a native ChatGPT slash command, an installed integration, or a guarantee of repository access.

## Quick start
```text
/INTEL HELP
/INTEL What are the seven knowledge domains?
/INTEL QUERY: Explain context engineering with sources.
/INTEL UI: Compare memory, context, and knowledge.
/INTEL REVIEW: Evaluate this response against the quality standards.
```

To work in a fresh chat, ChatGPT must first be given the [activation instructions](guides/chatgpt-activation.md) through an applicable instruction surface. It must also have a genuinely accessible copy of the repository (for example, through a connected GitHub source, or uploaded files). Typing a prefix alone cannot install those capabilities.

## Commands
| Command | Intent | Expected outcome |
| --- | --- | --- |
| `/INTEL` | Help | Explain available commands, current source access, and limits |
| `/INTEL HELP` | Help | Show examples and activation requirements |
| `/INTEL STATUS` | Status | Report source connection, fetched revision, and verification gaps |
| `/INTEL QUERY: <question>` | Reference lookup | Fetch relevant files, quote paths and revision, answer grounded in sources |
| `/INTEL RESEARCH: <question>` | Evidence review | Separate product evidence, hypotheses, limitations, and dates |
| `/INTEL DESIGN: <problem>` | Concept development | Propose design, alternatives, trade-offs, and acceptance criteria |
| `/INTEL UI: <task>` | Intelligent presentation | Design content structure first, then use only supported useful UI |
| `/INTEL REVIEW: <material>` | Quality review | Evaluate against relevant project quality criteria |
| `/INTEL SOURCE: <path>` | Source inspection | Read a canonical file and report its exact path/revision |

Plain `/INTEL <question>` is treated as `QUERY` if its intent is clear. Command names are case-insensitive. Unknown commands return HELP, rather than inventing behavior.

## Required behavior
1. Confirm which repository and branch/revision the conversation can **actually** read.
2. Resolve task-relevant sources through [the repository index](README.md) and canonical domain READMEs.
3. Fetch the relevant source content. **Do not infer that a file was read merely because a user provided a URL.**
4. Separate retrieved documentation, current verified product capabilities, proposed mechanisms, and unsupported claims.
5. Form the information architecture first; choose the simplest useful ChatGPT UI presentation afterward.
6. Cite the repository path and revision or supported file reference. Distinguish source evidence from the assistant's own interpretation.
7. If repository access fails, explicitly say `source unavailable`, provide a safe general answer only when useful, and do not claim `/INTEL` accessed GitHub.
8. Assume **read-only** behavior unless the user explicitly authorizes a specific write. A command prefix is never write permission.

## What activation means
| Surface | How to enable | Limitation |
| --- | --- | --- |
| This chat | Give the instructions and connect a readable source | Chat context alone is not durable installation |
| ChatGPT custom instructions | Add a compact activation rule | Instructions do not grant tool access |
| ChatGPT Project | Add project instructions and relevant files/connections | Availability and source boundaries vary |
| Existing custom GPT | Configure its instructions and sources if eligible | Separate product constraints; do not assume native Memory |
| Plugin/app integration | Implement a real connector and tool boundary | Requires engineering, authentication, and testing |

## Do not confuse
The independent `/INTEL` convention concerns this **public documentation and UX research project**. An unrelated `/CTX` workflow, if connected, is not automatically imported, given the same permissions, or made public.

[Activation guide](guides/chatgpt-activation.md) | [Source resolution](architecture/activation-and-source-resolution.md) | [Intelligent UI decision model](architecture/intelligent-ui-decision-model.md)


## G0 executable reference boundary

A Python command parser and contract dispatcher are implemented under [`generators/`](generators/__init__.py). The reference package is **not installed as a ChatGPT-native command**. Existing commands retain their documented purposes; `QUERY`, `RESEARCH`, `DESIGN`, `UI`, `REVIEW`, and `SOURCE` return `HOST_REQUIRED` from the standalone runtime because no ChatGPT host adapter is configured.

`/INTEL GENERATE <TYPE>` recognizes `PROMPT`, `CONCEPT`, `DOCUMENT`, `IMAGE`, `DESIGN`, `THEME`, `BRAND`, `GIF`, `SLIDES`, `DIAGRAM`, `CHART`, `CODE`, `VIDEO`, `AUDIO`, `WORKFLOW`, and `PACK`. At the original **G0 foundation milestone**, all sixteen were planned and responded `CAPABILITY_UNAVAILABLE`. This is a historical contract description, **not current runtime availability**. Format incompatibilities produce `UNSUPPORTED_FORMAT`. Unknown types produce `UNKNOWN_GENERATOR`. No command grants external actions. See [G0 runtime contracts](architecture/generator-foundation.md).

## G1 local text MVP

The [G1 local runtime](architecture/text-runtime.md) implements `/INTEL GENERATE PROMPT`, `CONCEPT`, and `DOCUMENT` as **deterministic Markdown templates** in Python. These are available from the local Python API and `python -m generators` CLI, not as native ChatGPT slash commands. This paragraph describes the **G1 text MVP**, not the current generator set. Later phases added local image, design, theme, brand, GIF, slides and diagram runtimes, and explicit optional model adapters. Source references are never fetched merely by appearing in a brief, and no publishing is implicit.

Example (no file output):

```bash
python -m generators prompt --objective "Create a secure code review prompt" --audience "Engineers" --authorize-create
```

`--authorize-create` is explicit local CLI authority; a prompt or source cannot supply this permission. Use `--export-root <existing-directory> --filename <new-name>.md` for verified exclusive Markdown file creation. Existing legacy commands are unchanged and still require a configured ChatGPT host for research/query execution.

## G1.6 opt-in model runtime

The Python CLI accepts `--mode model` for `PROMPT`, `CONCEPT` and `DOCUMENT` with `--authorize-create --authorize-external --authorize-billable`. The provider adapter requires `OPENAI_API_KEY` and `INTEL_OPENAI_MODEL` in a trusted process environment. Without them, it returns `MODEL_UNAVAILABLE`. Without the additional grants it returns `PERMISSION_DENIED`, before any network request. The deterministic template is still the default, with no network access. No live model integration or native ChatGPT command was verified by CI. See [G1.6 model host](architecture/model-host.md).

## G1.7 Local MCP host

An **executable local MCP stdio server** provides `generate_prompt`, `generate_concept` and `generate_document` through the existing Python `TextRuntime`. This is not a native ChatGPT slash command or proof of client installation. Start with `python -m generators.mcp_server --allow-create`; model mode also requires explicit external and billable startup permissions and separately configured API credentials. The default mode never calls an external provider. See [MCP host and live verification](architecture/mcp-host.md).
## Current executable local command reference (Phase 07)

This section is the current **local implementation** reference. The conversational /INTEL convention above remains separate, and historical G0/G1 descriptions describe their original milestone only.

- **Entrypoints:** intel.cmd (Windows launcher), python intel.py (cross-platform Python CLI), python -m generators (legacy generator parser), and scripts/intel.ps1 (Windows legacy actions).
- **Read-only inspection:** help, version, generators, capabilities, providers, status, doctor, config show, config validate, dev, clean, update, and logs without explicit file.
- **Explicit preference writes:** setup --apply, config language en|de, config import PATH --apply; config export PATH creates a new allowlisted file and refuses overwrite.
- **Local execution:** generate TYPE --objective TEXT --authorize-create delegates to existing generator contracts. Optional providers require additional explicit permissions. test runs unittests; check and verify run trusted local scripts.
- **Lifecycle:** start is legacy foreground Windows tunnel. start --managed opts into a Windows supervisor; stop/restart only affect authenticated CLI-managed tunnels. They do not manage the host-owned MCP server.
- **Developer profiles:** doctor basic|full, check docs|tests|all|safety, verify mcp --authorize-local-create, verify release. Clean remains preview-only, update never fetches, and logs --file PATH reads bounded, best-effort-redacted local text.
- **JSON:** put --json before inspection/profile commands (for example python intel.py --json doctor full). For generators use --format json when supported; global JSON is not a generator output switch.

The runtime capability catalog lists **ten implemented generator CLI types**: prompt, concept, document, image, design, theme, brand, gif, slides and diagram. The foundation registry still lists **sixteen conceptual types**; it is not an implementation or live-provider availability assertion. Read [Local CLI](LOCAL_CLI.md) for exact syntax, [Runtime Architecture](architecture/local-runtime.md) for component boundaries, [Migration](guides/local-cli-migration.md) and [Extension](guides/local-cli-extension.md) for change procedures, and [Troubleshooting](guides/local-cli-troubleshooting.md) for failures.
