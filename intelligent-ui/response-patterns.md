---
title: Response Pattern Library
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Intelligent UI Response Patterns

## Principle
Design the answer and source requirements first. Choose a supported format only if it improves understanding.

## Decision matrix
| Task | Information architecture | Baseline format | Rich format condition |
| --- | --- | --- | --- |
| Definition | Definition, caveat | Paragraph | Usually unnecessary |
| Comparison | Shared criteria, conclusion | Table | User-adjustable assumptions |
| Workflow | Ordered steps, exceptions | Numbered steps | Useful decision branches |
| Trend | Time series, units, sources | Text or table | Verified chart data exists |
| Spatial task | Grounded places and relationships | Text | Accurate, supported map |
| Scenario | Known inputs and calculation | Table | Controls actually recalculate |
| Review | Findings, evidence, severity | Structured prose | Expandable evidence aids use |

## Worked examples

**Definition:** "What is context engineering?" Answer with a concise definition. Avoid decorative cards.

**Comparison:** "Compare memory, context and knowledge." A compact table with identical columns shows their different roles. Reference the [context boundary specification](../architecture/context-and-information-boundaries.md).

**Interactive scenario:** Show a control only after defining an exact formula, grounded input data, the valid range, and a working update action. If unsupported, use an explicit static calculation without inventing observations.

**Source-dependent answer:** The /INTEL convention requires retrieval of the relevant canonical source. If source access is unavailable, clearly label the answer as general rather than repository-grounded.

## Failure handling
Unsupported UI uses accessible Markdown; missing measurements do not become fictional charts; source claims require retrieval and citation; interactions must not promise actions they cannot perform.

## Acceptance
The output leads with its conclusion, preserves evidence and limitations, explains any visualization in text, and uses no nonfunctional controls.

[UI decision model](../architecture/intelligent-ui-decision-model.md) | [Response format selection](response-format-selection.md) | [Compatibility](../architecture/chatgpt-compatibility.md)
