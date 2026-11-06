---
title: G1.9 ChatGPT Host Integration - Feasibility and Contract
status: proposed
version: 0.1.0
updated: 2026-11-06
---

# G1.9 - ChatGPT host integration (proposed)

## Goal

Allow `/INTEL GENERATE PROMPT|CONCEPT|DOCUMENT` to use an *actually available*
ChatGPT host capability without adding a billable OpenAI API dependency. The
standalone Python CLI and stdio MCP server **cannot invoke the ChatGPT
conversation model directly**. An independent, authorized client integration
must expose a genuine model-generation adapter before this provider is offered
to end users.

## Boundaries and prerequisites

- Investigate which ChatGPT client/app transport and model-facing tools are
  genuinely available. Verify current platform documentation and account-level
  eligibility; do not infer capabilities from MCP stdio unit tests.
- A trusted host injects an adapter implementing `configured` and
  `generate(kind, brief) -> ModelOutput`. The adapter's output is untrusted.
- An independent verified/reachable `ToolDeclaration` identifies the actual
  host capability; no tool declaration or permission may be derived from a
  model prompt, retrieved source or a mere installed plugin name.
- Keep existing `Authorization(CREATE)` checks. If an eventual bridge performs
  external or paid actions, it requires separate deterministic permission checks
  and explicit opt-in; never silently route to `openai-api`.
- Preserve `ArtifactManifest` state transitions, Markdown validation, source
  provenance labels and registry capability states.
- Distinguish what is used inside an interactive ChatGPT session from what a
  local Python process can invoke. The host callback interface is not an API.

## Proposed acceptance checks

1. Record the selected client/transport and verified API/tool capability.
2. Prove a host tool can be detected and unavailable hosts fail closed.
3. Test all three generators end-to-end in the **actual** authorized ChatGPT
   client with a named build/revision and bounded input/output.
4. Verify that requests without CREATE cannot generate, and that malicious
   brief/source text cannot grant tool or external/billable permissions.
5. Verify no separate paid API key or network endpoint is required by the
   approved ChatGPT-host path, within applicable ChatGPT plan limits.
6. Record failures, output verification and explicit human/client review.
7. Publish deployment instructions only after reproducing the real client
   integration; until then, mark G1.9 BLOCKED/not run.

## Non-goals

No installation claims, model invocation through the current conversation,
unrestricted ChatGPT internal access, hidden paid API fallback, arbitrary
client automation, or release certification.
