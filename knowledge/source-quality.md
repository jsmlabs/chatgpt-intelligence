---
title: Source Quality and Knowledge Maintenance
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Source Quality and Knowledge Maintenance

## In plain language
Reliable knowledge requires knowing where a claim came from, what it applies to, and whether it is still current.

## How it works
1. Express the exact claim, not merely a topic.
2. Prefer primary documentation for product-specific facts.
3. Record the source URL, relevant passage or section, publication/update date if known, and verification date.
4. Note applicable model, plan, client, or product surface.
5. Separate directly supported claims from interpretations.
6. Flag uncertainty and schedule rechecks for volatile claims.
7. Update the canonical document and link to it rather than duplicating it.

## Practical example
Claim: "Feature X is available in client Y." A useful record includes a specific official feature page, access conditions, and a check date. A generic Help Center homepage alone is insufficient evidence.

## Limitations and failure modes
Sources can be outdated, ambiguous, or inaccessible. A citation does not establish truth without checking its relevance. No product capability is claimed verified by this guide.

## Acceptance criteria
Every consequential claim can be traced to a suitable source or is marked unverified; stale claims are identifiable; scope and dates are explicit.

## Evidence and scope
This article presents an **original project method**, not a verified description of ChatGPT internals or an account-specific capability. For changing product facts, consult the [compatibility rules](../architecture/chatgpt-compatibility.md) and the [OpenAI Help Center](https://help.openai.com/) as a discovery starting point. No live product test is claimed here.

## Related reading
[ChatGPT compatibility](../architecture/chatgpt-compatibility.md) and [Research method](../research/research-method.md).

## Claim record template

```yaml
claim: "Feature X is available in product Y"
classification: experimental
product: chatgpt
surface: web
model: not-confirmed
plan: not-confirmed
source_url: null
verified_on: null
conclusion: unverified
recheck_when: source-or-product-changes
```

Change the classification to `verified-capability` only after checking a suitable source or documented reproducible observation, including all material access conditions.

## Practical example

**Question:** Is an interactive answer possible in ChatGPT? The [GPT-6 model guide](https://help.openai.com/en/articles/20001354-gpt-6-and-other-models-in-chatgpt) describes Intelligent UI in eligible Chat environments (accessed 2026-11-06). The supported conclusion is limited to those environments; it does not establish universal availability across all plans, models, or older desktop apps.

## Trust and freshness
Prefer official feature documentation for product behavior, authoritative primary datasets for measurements, and explicit dated tests for observed behavior. A high-quality old source may still be stale. Record a new review date when rechecking; never update dates merely to make a document look current.

## Maintenance workflow
When a claim changes, update its canonical page, log the change, inspect inbound references, and distinguish superseded facts from historical observations.
