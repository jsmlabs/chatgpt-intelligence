---
title: ChatGPT Compatibility
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# ChatGPT Compatibility

## Purpose
Keep this knowledge base useful when ChatGPT models, clients, subscription plans, and features change. **A documentation date is not proof that a feature was independently tested on that date.**

## Three evidence classifications
| Classification | Meaning |
| --- | --- |
| `verified-capability` | An applicable primary source or reproducible test supports the claim, with source and verification date recorded. |
| `proposed-design` | A design principle or model this repository recommends; not a product capability claim. |
| `experimental` | A tentative observation or hypothesis that needs more verification. |

## Record product-dependent claims
Use these fields when needed:

```yaml
feature: example-feature
product: chatgpt
surface: web
model: not-confirmed
plan: not-confirmed
classification: experimental
verified_on: null
source_url: null
limitations:
  - Availability depends on the selected surface or account.
```

Do not assign `verified-capability` without evidence. `verified_on: null` means **not yet checked**.

## Important boundaries
- **Memory:** Public markdown cannot directly read, edit, or synchronize a user's ChatGPT memory.
- **Context:** Chats, projects, GPTs, connectors, and API applications can have different context and permission boundaries.
- **Prompts:** Repository templates cannot override higher-priority instructions or guarantee deterministic model behavior.
- **Intelligent UI:** Available formats and components depend on the ChatGPT client, product experience, and runtime capabilities.
- **Knowledge:** Stored sources may become stale; revisit time-sensitive assertions.
- **Privacy:** A public repository is not a place for personal chat logs, secrets, or unredacted memories.

## Verification procedure
1. Find the relevant current official documentation.
2. Record the exact product surface, model (if relevant), access conditions, and limitations.
3. Capture the source URL and verification date.
4. Where possible, reproduce the behavior and record the observed outcome.
5. Recheck when a dependency or ChatGPT feature changes.

## Primary documentation entry points
- [OpenAI Help Center](https://help.openai.com/)
- [OpenAI platform documentation](https://platform.openai.com/docs/)

These are reference entry points, **not** evidence of any individual feature. Specific claims require more specific citations.

## Example
A proposed memory design can be labeled `proposed-design` without claiming that native ChatGPT Memory supports its storage format. To mark a specific product capability `verified-capability`, provide an exact official source or repeatable observation and record surface, access conditions, and verification date.

## Failure modes
- Assigning a current model name to an untested surface.
- Confusing a project proposal with a product feature.
- Using generic documentation entry points as evidence for specific behavior.
- Assuming identical support across clients or plans.

## Acceptance criteria
- Each changeable capability claim includes applicable evidence and a date, or is explicitly unverified.
- Plan, model, and interface scope are recorded where material.
- The three classifications are applied consistently.
- Unavailable or unknown capabilities are not represented as implemented.

[Documentation contracts](documentation-contracts.md) | [Architecture overview](overview.md)
