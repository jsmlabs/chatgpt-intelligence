---
title: INTEL G0 Runtime Contracts
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G0 runtime contracts

This is a dependency-free Python **reference runtime**, not a native ChatGPT integration. Canonical generator names and phase policy are in [GENERATOR-ROADMAP](../GENERATOR-ROADMAP.md). Existing seven domains and the original closed documentation roadmap are unchanged.

## Boundaries

1. `parse_command` recognizes the documented legacy namespace and `GENERATE <TYPE>`; no model parsing or implicit authority.
2. `Registry` owns unique generator identities, aliases, input descriptors, formats, required tools, risk and implementation states. All 16 generators are `planned`.
3. `Coordinator.dispatch` validates format/objective, checks fixed caller-provided permissions and verified tool evidence, then locates an explicitly registered adapter. It does not call third-party APIs by default.
4. `ArtifactManifest` records immutable identity, editable revision lineage, validation metadata and guarded lifecycle transitions. Export requires a non-empty, safe local file checked by `record_verified_output(reference, root)` and checked again at export time. The package does not write artifacts or verify remote/provider references.
5. `IntelError` returns machine-readable codes; audit events omit user content and credentials.

## Integration model

`/INTEL`, `HELP` and `STATUS` return local G0 metadata. Legacy task commands return `HOST_REQUIRED`, preserving their documented meaning but not pretending to have executed research. A host integration must authenticate, authorize, validate the request, bind adapters and report genuinely checked source provenance. Registration alone never implies operability. Adapter `reachable` and `verified` flags must originate from host evidence, not model text. The toy adapter tests prove only deterministic boundaries.

Supported adapter families: `text`, `image`, `document`, `design`, `animation`, `diagram`, `code`. No provider endpoints, storage engine, file writer, billable actions, network tool or deployment credentials are installed. Missing tools and adapters fail closed.

Permission vocabulary: `read_external_sources`, `read_local_files`, `create_artifacts`, `modify_artifacts`, `write_repositories`, `invoke_external_services`, `publish_or_deploy`, `execute_code`, `billable_operations`. The caller must supply a trusted `Authorization` instance; command arguments and sourced content cannot add grants. Guard output destinations using `safe_relative_path` and `verify_file`; these checks are not a replacement for sandboxed, race-safe filesystem writes at an integration boundary.

## Check

```bash
python -m unittest discover -s tests -v
python scripts/check_docs.py --root .
```

Deployment, ChatGPT-native activation, real adapter operations, output rendering, live storage and external side effects remain **NOT RUN / unavailable** in G0. G1 can implement text adapters without changing the dispatcher.
