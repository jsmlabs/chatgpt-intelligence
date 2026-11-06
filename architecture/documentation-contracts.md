---
title: Documentation Contracts
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---

# Documentation Contracts

## Overview
A lightweight set of rules that keeps documents easy to read and easy to maintain without introducing tooling that the project does not need.

## File and ownership conventions
- Name documents in descriptive English `kebab-case.md`.
- Each topic has a single canonical owner; link from other areas.
- Use relative links within this repository.
- Create new folders only when meaningful contents exist.
- Add a short, plain-language opening before advanced terminology.

## Suggested metadata
Use YAML frontmatter for substantial concept and specification documents. Top-level navigation files and small guides may omit it.

```yaml
---
title: Clear Document Title
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: proposed-design
---
```

### Status vs. evidence
| Field | Allowed values | Purpose |
| --- | --- | --- |
| `status` | `draft`, `proposed`, `accepted`, `deprecated` | Editorial or design decision lifecycle |
| `classification` | `verified-capability`, `proposed-design`, `experimental` | Evidence level or design nature |
| `version` | Version string | Revision of the document, not model or product |
| `updated` | ISO date | Date of document edit, not evidence verification |

When documenting changing ChatGPT features, additionally capture the product surface, model if relevant, plan or access conditions, source, verification date, and limitations. See [compatibility](chatgpt-compatibility.md).

## Recommended document sections
- Overview: what is this?
- Purpose: why does it matter?
- Decision model or how it works.
- Example: one realistic application.
- Limitations and failure modes.
- Acceptance criteria or next verification.
- Related reading.

Only include sections that genuinely help. Do not add empty boilerplate.

## Acceptance criteria
- Titles and filenames communicate purpose.
- Links resolve and terminology is consistent.
- Source-backed claims are distinguished from designs.
- The document remains understandable to a first-time reader.

## Related
[Contributing](../CONTRIBUTING.md) | [Document template](../templates/document-template.md)
