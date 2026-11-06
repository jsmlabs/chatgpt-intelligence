---
title: Research Method
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Research Method

## In plain language
Research turns a question into a reproducible finding rather than a confident guess.

## How it works
1. Write a narrow research question.
2. Define the target product, version, client, and evaluation conditions.
3. Collect relevant primary sources and record their dates.
4. Separate official claims, direct observations, and hypotheses.
5. Specify a reproducible procedure where feasible.
6. Record observations, counterexamples, limitations, and unanswered questions.
7. Publish a conclusion no stronger than the evidence supports.

## Practical example
Question: "Does a specific response format work in the selected client?" Record client and model, test input, observed output, and whether another user can repeat the procedure. Without a run, label the plan untested.

## Limitations and failure modes
A single successful example does not prove universal support. Product rollouts vary. Some internal mechanisms cannot be observed directly. Never fabricate test runs or source checks.

## Acceptance criteria
The research note contains question, method, evidence, date, scope, result status, and limitations; readers can distinguish planned tests from completed ones.

## Evidence and scope
This article presents an **original project method**, not a verified description of ChatGPT internals or an account-specific capability. For changing product facts, consult the [compatibility rules](../architecture/chatgpt-compatibility.md) and the [OpenAI Help Center](https://help.openai.com/) as a discovery starting point. No live product test is claimed here.

## Related reading
[Source quality](../knowledge/source-quality.md) and [Evaluation guidelines](../quality/evaluation-guidelines.md).

## Research record: practical checklist

For a claim about a changing ChatGPT capability, capture:

| Field | Example |
| --- | --- |
| Research question | Does a given model support visual answers in Chat? |
| Product and surface | ChatGPT, web, Chat |
| Model and plan | Record what was actually selected; do not guess |
| Source | Exact official help article and relevant section |
| Source reviewed | 2026-11-06 |
| Observation | Documented description, not a personal runtime test |
| Result | Source-supported, observed, inconclusive, or not-run |
| Limitations | Rollout, client, plan, and workspace conditions |

## Worked example: source-backed research
**Question:** Does ChatGPT GPT-6 support Intelligent UI in Chat?

**Source review:** The [GPT-6 Help Center article](https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt) describes text, visuals, and interactive elements at eligible thinking levels, with availability and client restrictions (accessed 2026-11-06).

**Conclusion:** The documentation supports a scoped product capability claim, not a guarantee that every user sees every component. **Runtime observation: not-run.**

## Common mistakes
- Treating a search snippet as equivalent to reading the source.
- Reporting a feature as universally available after one successful example.
- Calling a plan a successful test when no test was executed.
- Quoting a source without accounting for its dates or scope.
