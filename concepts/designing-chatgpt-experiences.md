---
title: Designing Better ChatGPT Experiences
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Designing Better ChatGPT Experiences

## In plain English
This repository studies a simple problem: **How can an assistant deliver the right information, in the right form, while respecting what matters to the user?**

This is a design problem with competing goals: accuracy, completeness, speed, readability, personalization, privacy, and control.

## A reference model, not model internals
We propose seven activities that can inform response design:
1. Understand the objective.
2. Resolve instructions and permissions.
3. Select relevant context.
4. Gather and verify evidence.
5. Plan the information hierarchy.
6. Select a useful output format.
7. Review the response against requirements.

Read the [Response Lifecycle](../architecture/response-lifecycle.md) for the canonical process. These activities do not describe or guarantee the model's hidden computation.

## Design trade-offs
| Trade-off | Better decision rule |
| --- | --- |
| Brevity vs completeness | Be concise without omitting required facts |
| Personalization vs relevance | Use preferences only when they materially improve the task |
| Interactivity vs simplicity | Add controls only when the user can do something useful |
| Freshness vs certainty | Verify changing facts, and report what remains unknown |
| Automation vs permission | Never treat available access as approval to write |

## Synthetic example
A user asks for a direct two-product comparison. An effective response states the central distinction, shows a compact table of genuinely comparable attributes, identifies evidence gaps, and provides a next step. A dashboard full of decorative widgets would make the answer less useful.

## Design review questions
- Can a beginner explain the purpose after reading the first paragraph?
- Is the model's conceptual status explicit?
- Which real user problem does each step solve?
- What happens when evidence is missing or requirements conflict?
- Is there a simpler approach with comparable clarity?
- Are privacy and authorization boundaries preserved?

## Failure modes
- Treating an attractive visual layout as proof of answer quality.
- Turning a preference into permission.
- Treating a proposed framework as a documented ChatGPT feature.
- Adding abstraction without a measurable benefit.

## Evidence boundary
Current Intelligent UI capabilities are described by OpenAI in [Intelligent UI in ChatGPT](https://help.openai.com/en/articles/20001598-intelligent-ui-in-chatgpt), reviewed 2026-11-06. Our seven-activity design framework is **not** claimed by that source.

## Acceptance criteria
- The concept has a clear reader benefit, process, and trade-offs.
- Examples demonstrate the concept without private information.
- Its status as a proposal is unmistakable.
- Future evaluations can compare it against simpler alternatives.

## Related reading
[Architecture Overview](../architecture/overview.md) | [Quality Standards](../quality/quality-standards.md)
