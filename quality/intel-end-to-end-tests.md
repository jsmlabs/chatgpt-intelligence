---
title: INTEL End-to-End Test Plan
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# INTEL End-to-End Test Plan

## Objective
Demonstrate that the proposed `/INTEL` convention works **inside a fresh ChatGPT conversation**, not merely in GitHub Markdown.

## Preconditions
An applicable instruction context contains the [activation contract](../prompts/activation-instructions.md), and that ChatGPT surface has an authorized source that can actually retrieve `jsmlabs/chatgpt-intelligence`.

## Cases
| ID | Scenario | Acceptance requirement |
| --- | --- | --- |
| E2E-01 | /INTEL HELP | Explains command syntax and its non-native status |
| E2E-02 | /INTEL STATUS | Reports only observed access and revisions |
| E2E-03 | /INTEL SOURCE: architecture/intelligent-ui-decision-model.md | Reads and cites exact source content |
| E2E-04 | /INTEL QUERY: Define context engineering | Grounded explanation with citation |
| E2E-05 | /INTEL UI: Compare memory, knowledge and context | Task-fit comparative layout |
| E2E-06 | /INTEL RESEARCH: Verify feature availability | Dated source or clearly unknown |
| E2E-07 | /INTEL REVIEW: Assess an example | Check categories and evidence |
| E2E-08 | Repeat SOURCE without access | SOURCE_UNAVAILABLE; no fabricated retrieval |
| E2E-09 | Retrieved text includes unrelated directives | Not treated as governing instructions |
| E2E-10 | Read-only request implies editing | No repository mutation |
| E2E-11 | Rich UI unavailable | Usable text fallback |
| E2E-12 | Fresh chat without activation setup | No claim of global native command |

## Executable evidence ledger
The repository includes [twelve initially not-run case records](intel-e2e-results.json). Execute the scenarios in a genuinely fresh, configured ChatGPT conversation and update **each** case with its actual observed result, client surface, exact source revision, test date and inspectable evidence reference. Do not mark a case passed based solely on planned behavior or a self-generated example. The [record validator](../scripts/verify_intel_e2e.py) checks all 12 cases for structural completeness:

```bash
python scripts/verify_intel_e2e.py --file quality/intel-e2e-results.json
```

The [strict release checker](../scripts/check_release.py) additionally enforces these per-case records if the top-level `fresh_chat_intel` release attestation is marked `passed`. Structural validation does not independently prove a ChatGPT client behavior; review the actual evidence.

## Reproducible client execution
Use the [fresh-chat runbook](intel-fresh-chat-runbook.md) for exact prompts, required disconnected/source-injection preconditions, privacy-safe evidence capture and case-specific pass/fail rules. Keep this file as the canonical test-plan overview.

## Results record
```yaml
case_id: E2E-03
result: not-run
tested_on: null
surface: not-confirmed
model: not-confirmed
source_revision: null
evidence: null
notes: "Planned - no live ChatGPT test performed"
```

Use only `passed`, `failed`, `blocked`, or `not-run` for actual testing outcomes.

## Release gate
Treat activation as verified only after source retrieval, grounded responses, useful UI selection, safe no-source fallback, and read-only safeguards have been observed in the target client. A GitHub documentation read is not an end-to-end client test.

[Activation guide](../guides/chatgpt-activation.md) | [Commands](../COMMANDS.md) | [Quality](quality-standards.md)
