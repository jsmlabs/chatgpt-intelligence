---
title: G2.4 BRAND deterministic generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G2.4 - BRAND Generator

## Scope

The local BRAND generator produces deterministic, editable **brand identity
briefs**, **machine-readable brand JSON**, and **static geometric SVG mark
concepts**. It reuses the exact G2.3 THEME token implementation and audited
light/dark color-pair contrast calculations. This is not an image-model
integration, design approval, rights clearance, or a production branding
system.

| Format | Deliverable | Verification boundary |
| --- | --- | --- |
| `markdown` | Positioning, audience, values, three directions, usage and review rules | Structural validation |
| `json` | Identity metadata, logo directions, selected direction, embedded G2.3 theme tokens and audits | Schema-specific checks, color-pair audit |
| `svg` | Standalone 512x512 fixed-geometry mark concept | Parsed XML, safe elements and attributes |

Three geometric directions are available: `orbit` (concentric structure),
`signal` (pulse line) and `aperture` (modular geometry). The mark uses
the same accent as the JSON token data. The logo concept is **not guaranteed
unique or trademark-safe**. No external fonts, asset URLs, script,
`foreignObject`, arbitrary paths or outside images are loaded.

Required inputs: `objective`, `name`. Optional: `audience`, `style`,
`values` (up to eight), `preset` (graphite/ocean/plum/forest),
`accent` (six-digit hex), `direction`, `format`.

All output is deterministic for equivalent inputs. Each format is exported
separately; this milestone does not implement ZIP packaging or a transactional
multi-file bundle. Untrusted user-supplied names are escaped in Markdown/XML.
No paid or external provider is invoked.

## Windows CLI

Run in the repository directory:

```powershell
python -m generators brand --objective "Research-driven developer tooling" --name "Example Labs" --audience "Developers" --value "Clarity" --value "Reliability" --preset ocean --direction orbit --format markdown --authorize-create
```

To export JSON and SVG files, choose an already existing directory:

```powershell
python -m generators brand --objective "Research-driven developer tooling" --name "Example Labs" --preset ocean --direction orbit --format json --authorize-create --export-root . --filename brand-tokens.json
python -m generators brand --objective "Research-driven developer tooling" --name "Example Labs" --preset ocean --direction orbit --format svg --authorize-create --export-root . --filename brand-concept.svg
```

Prefer an output directory **outside the public Git repository**. Existing
files are never overwritten; completed export requires byte-for-byte readback
and SHA-256 verification.

## MCP and review

The additive MCP tool `generate_brand` accepts the same structured inputs
and returns in-memory content plus a typed manifest and validation evidence.
It requires the trusted process `--allow-create` grant and does not write
files through MCP. Default tool discovery: **12** tools (**13** if the
separately opted-in ComfyUI image tool is enabled). Existing tools remain.

Automated tests cover output determinism, G2.3 token equality, multiple
mark directions, SVG/XML restrictions, escaped untrusted text, invalid
inputs, denied provider and create permissions, CLI and MCP contracts,
exclusive exports and readback hashes.

Human brand review, SVG visual inspection, legibility at small dimensions,
product/application rendering, trademark similarity and legal rights
clearance, live Windows execution and ChatGPT-client E2E are **not run**.
Passing automated SVG validation does not establish any of these.

[THEME](theme-generator.md) | [DESIGN](design-generator.md) |
[Generator roadmap](../GENERATOR-ROADMAP.md)
