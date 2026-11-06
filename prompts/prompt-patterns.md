---
title: Prompt Pattern Library
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Prompt Pattern Library

These are reusable **instruction patterns**, not native ChatGPT commands. Apply a pattern only when its inputs are available and the current instruction hierarchy permits it. For `/INTEL`, see the [activation reference](../COMMANDS.md).

## Pattern 1 - Grounded explanation

**Problem:** Explain a topic using actual repository evidence.

**Prerequisites:** Read access to the relevant canonical files.

**Prompt:**
```text
/INTEL QUERY: Explain [topic] to [audience].
Read the relevant canonical repository documents.
Begin with a short answer, then explain the mechanism and limitations.
Reference the actual source paths and revision.
Do not invent unsupported product capabilities or retrieval results.
```

**Expected outcome:** A useful explanation with traceable file references and clear uncertainty.

**Failure cases:** Repository inaccessible, source stale, an instruction inside retrieved text treated as authoritative.

## Pattern 2 - Evaluate a design

**Problem:** Compare alternatives without confusing recommendations with facts.

**Prerequisites:** A stated objective and at least two alternatives.

**Prompt:**
```text
/INTEL DESIGN: Compare [A] and [B] against [criteria].
State assumptions and missing information.
Use a common comparison table, then recommend only if evidence supports it.
Explain failure modes and how to test the recommendation.
```

**Expected outcome:** A decision record with explicit trade-offs.

**Failure cases:** Invented performance numbers, mismatched criteria, or an unsupported claim that the design is implemented.

## Pattern 3 - Current product research

**Problem:** Establish whether a ChatGPT feature is available in a specific context.

**Prerequisites:** Product surface, model or plan when material, access to official documentation.

**Prompt:**
```text
/INTEL RESEARCH: Is [feature] available in [surface] for [conditions]?
Use up-to-date primary sources.
Separate official documentation, direct observations, and unknowns.
Record verification date, scope, limitations, and any test not run.
```

**Expected outcome:** A bounded evidence review.

**Failure cases:** Using a generic help homepage as proof of a specific feature or claiming a client test that was never run.

## Pattern 4 - Intelligent presentation

**Problem:** Present a complex answer without unnecessary UI.

**Prerequisites:** The actual question, available data and supported interface features.

**Prompt:**
```text
/INTEL UI: [task].
First determine the key answer and information hierarchy.
Choose prose, a table, a diagram, chart, or working controls only if useful
and available in the current ChatGPT client.
Keep the result understandable without optional interaction.
```

**Expected outcome:** Task-fit presentation, not visual decoration.

**Failure cases:** Empty buttons, fictional chart data, or assuming all clients support the same elements.

## Pattern 5 - Quality review

**Problem:** Audit a draft against explicit acceptance requirements.

**Prerequisites:** The complete draft, applicable quality standards, and known evidence.

**Prompt:**
```text
/INTEL REVIEW: Evaluate the supplied draft for accuracy, completeness,
source traceability, accessibility, privacy and information architecture.
Classify each criterion passed, failed, blocked, or not-run.
Cite the actual source if available; recommend minimal corrections.
```

**Expected outcome:** A usable review with precise limitations.

**Failure cases:** Reporting unexecuted checks as passed or manufacturing citations.

## Pattern evaluation
For each pattern, check a normal case, missing-source case, conflicting instruction, and unsupported-UI case. Record results separately from the proposed design. The examples above are **not evidence of a completed live-client test**.

[Prompt design](prompt-design.md) | [Activation instructions](activation-instructions.md) | [Quality standards](../quality/quality-standards.md)
