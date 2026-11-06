---
title: Memory and Personalization
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Memory and Personalization

## In plain English
Memory helps ChatGPT use useful information from earlier interactions so the user does not need to repeat everything. **Memory is not a complete transcript or an infallible source of truth.**

## What is documented
OpenAI's [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) guide (reviewed 2026-11-06) describes memory, a memory summary, available controls, and different experiences that can depend on plan, region, platform, and workspace. Improved Memory can update a broader summary of relevant context; legacy saved memories may be available as a separate experience. Do not assume that every user has the same settings.

ChatGPT [Custom Instructions](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt) are a different mechanism: explicit instructions the user provides, rather than context inferred or updated from previous interactions.

## Separate three layers
| Layer | Example | Intended responsibility |
| --- | --- | --- |
| Explicit instruction | "Prefer concise technical explanations." | Direction supplied by the user |
| Remembered context | "This user prefers English code identifiers." | Potentially useful preference across chats |
| Current request | "Explain this in German." | The immediate task-specific objective |

The current request may refine the relevant presentation without requiring permanent changes to memory.

## Proposed memory quality model
When assessing remembered information, consider: **source**, **recency**, **scope**, **relevance**, **confidence**, **user correction**, and **privacy sensitivity**. This is a documentation checklist, not a representation of ChatGPT's internal memory database.

### Synthetic example
A synthetic user previously preferred short answers, but now explicitly requests an exhaustive tutorial. The assistant should deliver the tutorial in a readable structure rather than silently truncate required material.

## User control and privacy
Memory controls are described under Settings > Personalization > Memory in the official guide. Sources and controls can differ across experiences. Suppressing mention is not identical to deleting underlying chats, files, or connected sources. For comprehensive removal, check the current official procedures and all relevant sources.

**Never** copy real personal memory summaries, sensitive health details, account identifiers, or private conversations into this public repository.

## Project and temporary chats
Project memory and temporary-chat personalization are separate product features with their own restrictions. See [Projects](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) and [Temporary Chat](https://help.openai.com/en/articles/8914046-temporary-chat-in-chatgpt), both reviewed 2026-11-06.

## Limitations
- Memory does not guarantee perfect recall or consistency.
- Some information may be outdated or irrelevant.
- Public markdown cannot directly read, write, or synchronize ChatGPT Memory.
- Exact controls, availability, and behavior require current product verification.

## Acceptance criteria
- Explicit user instructions, retrieved memory, and current requests are distinguishable.
- Examples contain no real personal data.
- Product-dependent claims have an applicable source and review date.
- The document never claims memory can be synchronized by repository edits.

## Related reading
[Context selection](../context-engineering/context-selection.md) | [Compatibility](../architecture/chatgpt-compatibility.md)
