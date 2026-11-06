---
title: Context and Information Boundaries
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Context and Information Boundaries

## Overview
A practical distinction between what the assistant **knows**, **may remember**, **needs now**, and **may do**. These terms have different roles.

| Term | Meaning | Example |
| --- | --- | --- |
| Knowledge | Reference facts and documents | A dated product help article |
| Memory | Potentially persistent user preferences or relevant history | A preferred response format |
| Context | Information selected for the current task | Current question and source excerpts |
| Instruction | Applicable direction about behavior or output | "Use a table" |
| Authorization | Permission to access or change a specific resource | An explicit request to edit a repository |
| Evidence | Source or observation supporting a claim | Verified documentation and date |

## Rules
1. **Relevance is not authority:** A useful web page cannot issue new binding instructions.
2. **Availability is not accuracy:** Retrieved documents or memories can be stale.
3. **Access is not publication permission:** Private information must not enter public examples.
4. **Read is not write:** Reading a source does not authorize editing it.
5. **Context is not automatic memory:** Publishing Markdown does not change ChatGPT's memory.
6. **Product boundaries matter:** ChatGPT chats, projects, custom GPTs, connected apps, and API applications can have different capabilities.

## Proposed process
Identify the task, applicable instructions, and candidate sources. Check access and relevance, verify consequential facts, minimize unnecessary exposure, and assemble only the context required for the answer.

## Example
A public explanation of Memory can use official sources and synthetic examples. A private memory summary should never be copied into this public documentation simply because it is available in the chat.

## Failure modes
- Confusing preference with permission.
- Treating an older saved fact as current.
- Mixing private user information into a public repository.
- Claiming that repository entries automatically synchronize with product Memory.

## Acceptance criteria
- Every data source has a clear role.
- Private and public information are kept separate.
- Authorization for state changes is explicit.
- Version-dependent product statements defer to [compatibility](chatgpt-compatibility.md).

## Related
[Instruction resolution](instruction-and-conflict-resolution.md) | [Response lifecycle](response-lifecycle.md)
