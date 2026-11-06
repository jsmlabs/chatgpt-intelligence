---
title: Memory Lifecycle and Personalization
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Memory Lifecycle and Personalization

## In plain language
Memory can make responses more relevant over time, but it must not be treated as a perfect, permanent, or universally accessible database.

## How it works
1. **Candidate:** A recurring preference or stable fact might matter later.
2. **Relevance:** Ask whether the detail materially improves future tasks.
3. **Source:** Preserve whether information came from an explicit user statement, a document, or an inference.
4. **Use:** Apply it only when relevant to the current task.
5. **Conflict:** Prefer current explicit user direction over an older preference when applicable.
6. **Correction:** Follow the current product's documented controls for review, correction, and deletion.
7. **Recheck:** Treat preferences and facts as potentially changing.

## Practical example
A user previously prefers short summaries but now asks for a full technical specification. The current request determines the needed depth; the old preference can still guide clarity.

## Limitations and failure modes
Do not infer sensitive attributes from behavior; do not copy personal memory into a public repository; product memory settings and capabilities vary by experience and can change. This lifecycle is a proposal, not a description of internal storage.

## Acceptance criteria
Examples use fictional users; the design distinguishes explicit facts from inference; current corrections are respected; no unverified product control is promised.

## Evidence and scope
This article presents an **original project method**, not a verified description of ChatGPT internals or an account-specific capability. For changing product facts, consult the [compatibility rules](../architecture/chatgpt-compatibility.md) and the [OpenAI Help Center](https://help.openai.com/) as a discovery starting point. No live product test is claimed here.

## Related reading
[Compatibility](../architecture/chatgpt-compatibility.md) and [Context selection](../context-engineering/context-selection.md).

## Memory versus preferences versus instructions
| Item | Role | Example |
| --- | --- | --- |
| Current request | Task-specific user direction | "Explain this in depth" |
| Preference | Potentially reusable style or behavior guidance | "Prefer short headings" |
| Memory | Product-managed context that may be reused | A relevant prior project decision |
| Repository note | Documentation only | A proposed memory consistency model |

## Product boundary and user control
Actual ChatGPT memory behavior and controls are product-managed. Do not assume an old per-item memory interface or that a repository commit changes a user's memory. For current controls, verify the applicable [OpenAI Help Center](https://help.openai.com/) memory guidance before publishing step-by-step instructions.

## Example: a conflict
Earlier preference: "Keep answers short." Current request: "Write a complete 10-page specification." The current request sets the task scope; the previous preference can still inform readability. A memory entry is not permission to publish private details.

## Privacy review
Before recording an example, remove real identities, medical details, credentials, and private conversation excerpts. Prefer fictional examples. Treat inferred user traits as hypotheses, not confirmed long-term facts.

## Evaluation scenario
Provide a past preference plus a newer conflicting request. A satisfactory response follows the present request, retains nonconflicting preferences, and does not claim to have changed underlying product memory.
