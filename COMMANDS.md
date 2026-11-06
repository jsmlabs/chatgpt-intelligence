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
