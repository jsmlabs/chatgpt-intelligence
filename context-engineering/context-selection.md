---
title: Context Selection and Boundaries
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Context Selection and Boundaries

## In plain English
Context engineering means giving an AI assistant the **right information for this task**. More information is not automatically better. The useful context is accurate, relevant, permitted, and current enough for the decision.

## Why it matters
Without a clear selection process, a response can become distracted by old preferences, treat external text as instructions, or accidentally repeat confidential details.

## Six context questions
1. **Goal:** What outcome did the user request?
2. **Authority:** Which instructions actually apply? Retrieved documents are evidence, not new higher-priority commands.
3. **Relevance:** Which facts or preferences materially affect this particular answer?
4. **Freshness:** Must any information be checked against a current source?
5. **Permissions:** May this information be read, used, or published in this setting?
6. **Sufficiency:** Can the task be completed without adding more context?

## Example: choosing a response format
The user asks: "Compare memory and context engineering in two columns." The relevant context is the actual question, applicable formatting instructions, and grounded definitions. Their unrelated past shopping preferences add no value. The response should contain a concise two-column comparison, not a personal profile.

## Context is not memory, knowledge, or permission
| Concept | Question it answers |
| --- | --- |
| Context | What information is needed right now? |
| Knowledge | What information can be referenced and supported? |
| Memory | What potentially relevant information persists across interactions? |
| Instruction | What behavior is required? |
| Authorization | What actions and disclosures are allowed? |

A file can contain all five sorts of information, but its mere presence does not give it authority or permission.

## ChatGPT product boundaries
ChatGPT Projects can provide project instructions, chats, and files. Project-only memory changes which outside context may be referenced; shared projects use project-only memory. These are product features, not universal behavior for every ChatGPT surface. See [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) (reviewed 2026-11-06).

## Proposed selection procedure
Start from the request, enumerate candidate sources, remove irrelevant or unauthorized material, verify changing facts, identify conflicts, and use the smallest sufficient selection. Revisit the selection if the task changes.

## Failure cases
- A pasted page tells the assistant to ignore the user's instruction.
- An outdated project note is treated as current evidence.
- The assistant republishes private context into a public deliverable.
- The user asks for a direct answer but receives extensive irrelevant personalization.

## Acceptance criteria
- The chosen context has a documented reason to be included.
- Lower-trust content is not promoted into instructions.
- Privacy boundaries and uncertainty are explicit.
- The output satisfies the task without unnecessary context.

## Related reading
[Instruction conflict resolution](../architecture/instruction-and-conflict-resolution.md) | [Memory](../memory/README.md) | [ChatGPT compatibility](../architecture/chatgpt-compatibility.md)

## Source selection worksheet

| Candidate information | Use? | Why? |
| --- | --- | --- |
| Current task requirements | Yes | Defines the outcome |
| Relevant project specification | Usually | Supplies applicable constraints |
| Dated official product source | When feature-dependent | Reduces risk of stale capability claims |
| Old unrelated preference | No | Does not materially improve the answer |
| Instructions embedded in a retrieved page | No, as authority | External text is task data, not an instruction source |
| Private details in a public deliverable | No | Access does not authorize publication |

## Change handling
When the user updates one requirement, preserve the other compatible constraints. Re-evaluate context only for the changed task dimensions instead of rebuilding an unrelated personal profile.

## Product evidence limit
The [Projects in ChatGPT documentation](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) confirms that projects group chats, files, and instructions (reviewed 2026-11-06). Project-specific capabilities and memory settings are not universal across unrelated products or accounts.

## Acceptance exercise
Given a request to publish a general tutorial and a private project excerpt, select only the facts needed for a public explanation. The result should avoid reproducing secrets and should cite any changing public capability claims.
