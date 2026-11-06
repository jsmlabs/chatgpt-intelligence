---
title: Concept Development
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Concept Development

## In plain language
A concept is a reasoned proposal for solving a problem, not proof that a feature exists.

## How it works
1. Describe the user problem in plain language.
2. Define the desired outcome and non-goals.
3. List assumptions and known constraints.
4. Propose the simplest workable mechanism.
5. Compare at least one alternative when trade-offs matter.
6. Describe failure modes, privacy implications, and dependencies.
7. Define how the concept could be evaluated before calling it accepted.

## Practical example
Concept: "Select response formats based on information shape." Alternative A always uses prose; alternative B always uses rich UI. The proposed approach chooses formats only when they improve comprehension. Evaluate with comparable example tasks.

## Limitations and failure modes
A concept can be accepted as a project design without being implemented or validated in ChatGPT. Avoid describing hypothetical internal pipelines as facts.

## Acceptance criteria
The problem, mechanism, alternatives, trade-offs, evaluation criteria, and status are explicit; product capability claims are separately evidenced.

## Evidence and scope
This article presents an **original project method**, not a verified description of ChatGPT internals or an account-specific capability. For changing product facts, consult the [compatibility rules](../architecture/chatgpt-compatibility.md) and the [OpenAI Help Center](https://help.openai.com/) as a discovery starting point. No live product test is claimed here.

## Related reading
[Response lifecycle](../architecture/response-lifecycle.md) and [Documentation contracts](../architecture/documentation-contracts.md).

## Mini concept canvas

| Question | Proposed answer: adaptive response formatting |
| --- | --- |
| Who benefits? | Readers who need both speed and clarity |
| Problem | Decorative or poorly structured answers obscure essential information |
| Goal | Make key conclusions easy to locate |
| Constraints | Preserve accuracy; respect client capabilities; avoid inaccessible formats |
| Proposed mechanism | Plan content hierarchy first, then select the minimum useful presentation |
| Alternative | Always use prose or always use cards |
| Trade-off | Adaptive selection adds decision effort but may improve task fit |
| Verification | Compare responses across diverse questions using the same rubric |

## Decision record
Mark **proposed** while investigating and **accepted** only when the project agrees on the design. Acceptance does not mean implementation, empirical success, or official OpenAI endorsement.

## Reject or revise when
- The problem is not explained in user terms.
- The proposed mechanism depends on unconfirmed API or UI behavior.
- No meaningful comparison or test can distinguish alternatives.
- A simpler pattern already solves the problem.
