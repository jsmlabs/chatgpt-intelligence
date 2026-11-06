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
