---
title: INTEL Source Retrieval Smoke Test
status: accepted
version: 1.0.0
updated: 2026-11-06
classification: experimental
---

# INTEL Source Retrieval Smoke Test

## Scope
A real source retrieval check performed **inside the existing ChatGPT conversation** using its authorized GitHub connection. This is not a test in a new conversation and does not establish that the `/INTEL` prefix is installed or recognized automatically.

## Observed retrievals
| Path on main | Git blob SHA | Result |
| --- | --- | --- |
| [COMMANDS.md](../COMMANDS.md) | `ea7471224a789aa6be918eedbcec03337ea17f18` | passed - content fetched |
| [Intelligent UI decision model](../architecture/intelligent-ui-decision-model.md) | `c5763ce009799c9af02a50e7685cd3bce3b2476f` | passed - content fetched |
| [Context selection](../context-engineering/context-selection.md) | `225324ef27f1db37001b02ed0b669df5128d858a` | passed - content fetched |
| [Memory lifecycle](../memory/memory-lifecycle.md) | `34a3a014d5410bf7f886e24e15b06a47b8ca46f9` | passed - content fetched |
| [Source quality](../knowledge/source-quality.md) | `ae800980738a234d6a537aec92601fed03f7d9c2` | passed - content fetched |

## Test interpretation
- **Passed:** This connected chat can read canonical GitHub repository files and obtain verifiable blob identifiers.
- **Not-run:** A fresh-chat `/INTEL STATUS` or `/INTEL SOURCE` command invocation using configured activation instructions.
- **Not-run:** Native Intelligent UI response render testing in that fresh-chat context.
- **Not-run:** Disconnected-client fallback tests and authorization enforcement tests.

The above SHA values identify fetched file **blobs**, not one atomic repository commit. Recheck the exact branch revision if reproducibility across multiple documents is required.

## Follow-up gate
Complete E2E-01 through E2E-12 from the [end-to-end plan](intel-end-to-end-tests.md) in a freshly configured ChatGPT conversation. Capture the source commit SHA, exact tested model/client, command, result, observed answer, and any failure.

[Command reference](../COMMANDS.md) | [Roadmap](../ROADMAP.md)
