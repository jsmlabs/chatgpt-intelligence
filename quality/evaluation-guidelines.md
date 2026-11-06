---
title: Evaluation Guidelines
status: proposed
version: 0.1.0
updated: 2026-11-06
---

# Evaluation Guidelines

## Manual evaluation
For each document or example, ask:
- Is the central question answered?
- Are relevant claims supported?
- Is uncertainty explicit?
- Can a beginner understand the opening?
- Is the structure easy to navigate?
- Does every visual element add information value?
- Are limitations and privacy boundaries included when needed?

## Example outcome record
```yaml
case: documentation-review-001
target: architecture/response-lifecycle.md
result: not-run
reviewed_on: null
notes: Manual review pending
```

## Future work
Develop repeatable scenarios for instruction conflicts, stale source material, memory limitations, and complex UI selection. A future benchmark should not imply automated execution until it is actually implemented.

## Conversational end-to-end checks
See the [INTEL End-to-End Test Plan](intel-end-to-end-tests.md). The listed scenarios are **not-run** until observed in the actual ChatGPT client. The repository documentation audit cannot substitute for those results.
