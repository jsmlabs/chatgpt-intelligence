---
title: Response Lifecycle
status: proposed
version: 0.2.0
updated: 2026-11-06
classification: proposed-design
---

# Response Lifecycle

## Overview
A proposed reference workflow for producing useful, trustworthy responses. This is **not** a statement about ChatGPT's hidden model execution.

## Decision process
1. **Understand:** Identify the objective, output, constraints, and task type.
2. **Resolve:** Follow applicable instructions and address conflicts. See [instruction resolution](instruction-and-conflict-resolution.md).
3. **Gather:** Select relevant, permitted knowledge and memory. See [information boundaries](context-and-information-boundaries.md).
4. **Verify:** Check consequential or changeable claims against available evidence.
5. **Plan:** Choose information hierarchy, expected depth, and essential comparisons.
6. **Present:** Select the simplest useful supported format. See [Intelligent UI decision model](intelligent-ui-decision-model.md).
7. **Review:** Check correctness, completeness, evidence, privacy, and usability.

## Example
For a definition, a short paragraph is usually sufficient. For an exact comparison, a table often helps. For a branching workflow, a diagram may improve comprehension if supported.

## Failure modes and limits
A well-designed process does not guarantee correct model output. Available tools, context sources, memory, UI elements, and product behavior can change. A complicated format may obscure the answer; an overly short response may omit required information.

## Acceptance criteria
- The objective and all critical requirements are addressed.
- Relevant context is used without exceeding authorization or privacy boundaries.
- Important factual claims are adequately supported or marked uncertain.
- The presentation improves readability rather than merely decorating the answer.
- No internal model process or successful tool operation is claimed without evidence.

[Quality standards](../quality/quality-standards.md) | [Evaluation guidelines](../quality/evaluation-guidelines.md)
