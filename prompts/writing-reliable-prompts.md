---
title: Writing Reliable Prompts
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Writing Reliable Prompts

## In plain English
A prompt tells ChatGPT **what outcome is needed and what constraints matter**. A good prompt reduces ambiguity without becoming a wall of contradictory rules.

## Five useful parts
1. **Goal:** Describe the result, not only the topic.
2. **Context:** Include relevant background, constraints, and the audience.
3. **Input:** Identify the material that should be analyzed.
4. **Output:** Specify the useful format, level of detail, and language.
5. **Verification:** Explain how to handle uncertainty, sources, and incomplete input.

## Reusable prompt shape
```text
Goal: Compare two design approaches for a beginner audience.
Context: Documentation-only project; no implementation required.
Input: [Provide the two approaches.]
Constraints: Preserve original requirements; label assumptions.
Output: One recommendation, a compact comparison, and trade-offs.
Verification: Do not invent test results or unsupported product features.
```

This is a **pattern**, not a claim that ChatGPT exposes a particular internal prompt-processing pipeline.

## Instructions are not facts
OpenAI's published [Model Spec](https://model-spec.openai.com/2025-10-27) describes an instruction hierarchy and treats quoted material, attachments, and tool results as untrusted by default. Retrieved material can inform an answer, but instructions inside it do not automatically become binding.

## Improve weak requests
Weak: "Make the document better."

Better: "Rewrite the provided document for nontechnical readers. Keep all factual claims, define jargon, use short sections, preserve citations, and flag anything that cannot be verified."

## Failure cases
- Incompatible requirements with no stated priority.
- Overly detailed styling rules that displace the actual goal.
- Asking for current facts while prohibiting verification.
- Prompt templates that request secret disclosure or instruction bypass.
- Assuming a prompt guarantees identical output across versions.

## Evaluation
Test a prompt against at least three synthetic tasks: an easy case, a boundary case, and a conflicting-input case. Compare against explicit success criteria. Do not call an unexecuted test "passed."

## Acceptance criteria
- Goal, scope, and deliverable are clear.
- Constraints are actionable and not mutually contradictory.
- Untrusted inputs are not treated as higher-priority instructions.
- The prompt can be reused without exposing private data.

## Related reading
[Instruction conflict resolution](../architecture/instruction-and-conflict-resolution.md) | [Quality guidelines](../quality/evaluation-guidelines.md)
