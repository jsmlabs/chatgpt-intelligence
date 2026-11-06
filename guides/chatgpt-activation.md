---
title: Use ChatGPT Intelligence Inside ChatGPT
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Use ChatGPT Intelligence Inside ChatGPT

## What you can do
You can use a convention such as `/INTEL QUERY: ...` to request repository-grounded answers and suitable Intelligent UI in conversations where the instructions **and** a readable source are available. This is not a native slash command or an automatically installed integration.

## Setup A: use a ChatGPT conversation with a connected repository
1. Ensure the current chat can actually read `jsmlabs/chatgpt-intelligence` via its authorized GitHub source.
2. Provide the [activation instruction](../prompts/activation-instructions.md) in the applicable instruction context, or paste it into the conversation.
3. Enter `/INTEL STATUS`. Require the assistant to report whether it fetched a real path and commit.
4. Try `/INTEL QUERY: What is the difference between memory and context?`.
5. Try `/INTEL UI: Compare the seven domains by purpose and expected output.`.
6. Compare the cited GitHub files with the answer. Reject any invented source or unsupported UI claim.

## Setup B: ChatGPT Project or custom instructions
Place the compact activation instruction in the project's instruction field (or in account custom instructions if you explicitly want broad scope). Make the repository source available to that surface. A Project or custom instruction cannot turn an unavailable connector into an available one.

## Setup C: existing custom GPT or future plugin
Where eligible, an existing GPT can be configured with instructions and knowledge or connected sources. The ChatGPT product's current availability and edit policies may restrict GPT creation or modification. A dedicated plugin/app could implement retrieval and UI workflows but is **not delivered by this repository**.

## Expected demonstration
**Prompt:** `/INTEL UI: Compare memory, context and knowledge.`

**Expected behavior:** The assistant confirms source access, reads the domain material, writes a short definition, and may choose a three-row table. It cites the source path/revision and does not claim the repository changed product Memory.

## Fallback behavior
If GitHub is not available, say so and stop repository-grounded claims. If rich UI is unavailable, use a clear Markdown response. Neither case should result in fabricated file reads or decorative controls.

## Product documentation
- [ChatGPT custom instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions)
- [GPTs in ChatGPT](https://help.openai.com/en/articles/8554407-gpts-in-chatgpt)
- [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)

Sources can change. Treat these as current product references, not guarantees about this particular account's permissions.

[Command reference](../COMMANDS.md) | [Prompt instructions](../prompts/activation-instructions.md)
