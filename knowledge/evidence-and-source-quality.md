---
title: Evidence and Source Quality
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Evidence and Source Quality

## In plain English
Knowledge is useful when a reader can tell **what is known, how it is known, and when it might become outdated**. This document proposes a simple evidence workflow for the repository.

## Classify each important statement
| Kind | Meaning | Example |
| --- | --- | --- |
| Documented fact | Supported by a dated, applicable source | A Help Center page describes a feature |
| Observation | Reproduced in an identified setting | A test on web Chat produced a chart |
| Inference | Reasoned conclusion drawn from evidence | A simpler layout may reduce reading effort |
| Proposal | A rule or concept we recommend | Prefer tables for exact comparisons |
| Unknown | Not yet checked or not determinable | Whether a feature is available in an untested workspace |

The [compatibility taxonomy](../architecture/chatgpt-compatibility.md) additionally labels capabilities as `verified-capability`, designs as `proposed-design`, and hypotheses as `experimental`. Editorial approval is not evidence.

## Source hierarchy
1. Prefer official product documentation for current ChatGPT feature claims.
2. Prefer primary technical documentation for APIs and behaviors.
3. Use reproducible firsthand tests with recorded model, surface, and date.
4. Use secondary commentary for discovery and perspective, not as automatic proof.
5. For changing facts, inspect publication and update dates and recheck applicability.

## Example: feature claim
Claim: "ChatGPT Projects can incorporate project-specific files and instructions."

Evidence: [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt), reviewed 2026-11-06. Scope: ChatGPT Projects. Limitation: available context and memory mode may differ by plan, workspace, and sharing state.

**Incorrect extension:** "All ChatGPT chats automatically have access to every project file."

## Proposed evidence record
```yaml
claim: "Projects can use project files as context."
classification: verified-capability
product: chatgpt
surface: projects
source_url: https://help.openai.com/en/articles/10169521-projects-in-chatgpt
verified_on: 2026-11-06
limitations:
  - Access and project memory settings vary.
```

This metadata is a documentation convention, not an integration with OpenAI systems.

## Maintenance and privacy
When a source changes, either update the claim, scope it more narrowly, or mark it unverified. Prefer links to canonical definitions over copied paragraphs. Never publish customer records, personal chat histories, or secrets as demonstration evidence.

## Failure cases
- A stale article is treated as present-day product behavior.
- A general homepage is cited for a specific unsupported detail.
- A hypothesis is marked as tested.
- One observed account is generalized to all plans and regions.

## Acceptance criteria
- Every material changeable claim has an exact source and review date.
- Scope and limitations are explicit.
- Claims, proposals, and experiments are not conflated.
- Reader can follow the source without depending on private context.

## Related reading
[Compatibility](../architecture/chatgpt-compatibility.md) | [Research](../research/README.md) | [Quality standards](../quality/quality-standards.md)
