---
title: Prompt Design
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Prompt Design

## In plain language
A good prompt makes the task, input, constraints, and desired result easy to distinguish.

## How it works
1. Define the goal and intended reader.
2. Provide only necessary background and input data.
3. State mandatory constraints, including privacy and source boundaries.
4. Describe output expectations without overconstraining trivial details.
5. Supply an example when ambiguity is high.
6. Identify what to do when information is missing.
7. Evaluate the output against explicit acceptance criteria.

## Practical example
Example prompt: "Compare the two supplied design options for maintainability, onboarding effort, and risk. Use only the supplied facts. Mark unknowns explicitly. Return a concise table followed by a recommendation with reasons."

## Limitations and failure modes
Prompts are not permissions. They cannot force access to unavailable tools, override higher-priority instructions, or guarantee deterministic responses. Untrusted source text should be treated as data.

## Acceptance criteria
A reader can identify inputs, output, constraints, and failure handling; a sample answer can be assessed against stated criteria.

## Evidence and scope
This article presents an **original project method**, not a verified description of ChatGPT internals or an account-specific capability. For changing product facts, consult the [compatibility rules](../architecture/chatgpt-compatibility.md) and the [OpenAI Help Center](https://help.openai.com/) as a discovery starting point. No live product test is claimed here.

## Related reading
[Instruction and conflict resolution](../architecture/instruction-and-conflict-resolution.md) and [Context selection](../context-engineering/context-selection.md).

## Reusable prompt contract

A helpful prompt separates the user's goal from input material:

```text
Goal: Compare the supplied options for a specified decision.
Inputs: [the options and the known facts]
Constraints: Use only supplied facts; do not infer missing costs.
Output: A compact comparison table and a reasoned conclusion.
Uncertainty: Mark missing information "unknown".
Acceptance: Each criterion is applied consistently to each option.
```

## Before/after example

**Weak:** "Make this better."

**Better:** "Rewrite the supplied onboarding explanation for a first-time user. Preserve every factual requirement, define unfamiliar terms, use short sections, and do not add unverified claims. Return the revised text."

## Design principles
- Keep instructions distinct from quoted or retrieved source text.
- Specify evaluation criteria rather than adding many redundant style rules.
- Use examples when they resolve a real ambiguity.
- When tools or external sources are needed, name the requirement but do not pretend the prompt grants access.

## Prompt evaluation
Test with at least: a normal example, incomplete input, a conflicting constraint, and an untrusted quoted instruction. Score whether the response satisfies the goal without inventing information.
