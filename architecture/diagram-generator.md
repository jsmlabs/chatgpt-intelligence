---
title: G3.3 DIAGRAM Generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G3.3 - DIAGRAM Generator

## Implemented functionality

The deterministic, offline DIAGRAM runtime creates bounded, validated
**directed acyclic graphs** (DAGs) representing simple flowcharts or
service-architecture flows. It provides three interchangeable formats:

| Format | Deliverable | Validation |
| --- | --- | --- |
| `json` | Nodes, edges, stable layout coordinates, theme and provenance | Round-trip structured data |
| `mermaid` | Editable Mermaid `flowchart TB/LR` source (`.mmd`) | Deterministic serialization and input validation |
| `svg` | Standalone accessible-name SVG geometry | XML parser, allowlisted tags, label checks and no external resource references |

Allowed node types: `process`, `decision`, `service`, `database`.
Allowed directions: `TB` (top to bottom) and `LR` (left to right).
Limit: 1-16 nodes, 0-24 edges, unique lowercase node IDs and bounded
labels. Nodes connected by edges must exist. Self-edges, duplicate edges
and cycles are rejected. This milestone does **not** implement cyclic
flowcharts, clustering, swimlanes, sophisticated edge routing or
general Graphviz/Mermaid parsing.

A deterministic topological rank assigns layers and bounded integer
coordinates. The SVG renderer uses static rectangles/diamonds,
straight connectors, named arrows and text nodes. Large labels may
overflow their boxes; diagrams require a real viewer's visual review.

G2.3 palette presets `graphite`, `ocean`, `plum`, `forest`, plus
an optional six-digit accent, supply the output colors. The renderer
does not use a model, fetch external images, inject scripts or rely
on third-party packages.

## Local CLI

From the project directory:

```powershell
# JSON topology with fixed default three-node flow
python -m generators diagram --objective "Request lifecycle" --format json --authorize-create

# Explicit service architecture and standalone SVG export
python -m generators diagram --objective "API architecture" --diagram-kind architecture --diagram-direction LR --preset ocean --node "web|Web client|service" --node "api|API|process" --node "db|Database|database" --edge "web|api|request" --edge "api|db|query" --format svg --authorize-create --export-root . --filename architecture.svg

# Editable Mermaid flowchart
python -m generators diagram --objective "Review flow" --format mermaid --authorize-create
```

Prefer a dedicated export directory **outside** the Git repository.
The exporter refuses existing filenames, path traversal and mismatched
extensions, and verifies written bytes with SHA-256. Mermaid files
use `.mmd`; SVG and JSON use their standard extensions.

The CLI shorthand uses `id|label|type` and `source|target|label`.
Use the structured MCP request for text containing pipe delimiters.

## MCP tool

`generate_diagram` accepts objective, kind, direction, format, preset,
accent, nodes and edges under a bounded JSON schema. It returns
in-memory JSON, Mermaid or SVG text and manifest/evidence. No MCP
file export, model call, billing or publication occurs.

The default stdio host now advertises **15 tools** (or **16** with
separately opted-in ComfyUI image inference). Existing tool IDs remain
unchanged. The trusted process-level `--allow-create` grant is required.

## Verification boundary

Automated tests cover topological layers, deterministic Mermaid,
SVG XML parsing and escaping, invalid/cyclic graph rejection,
invalid or unknown references, denied permissions, safe exclusive
export, CLI and MCP integration.

The renderer's validation is **structural only**. Actual Mermaid
parser compatibility, browser SVG rendering, text-overflow detection,
diagram readability, keyboard/screen-reader testing, and visual
review are **not run**. It is not a general-purpose diagram editor.

[Generator roadmap](../GENERATOR-ROADMAP.md) |
[THEME generator](theme-generator.md) |
[DESIGN generator](design-generator.md)
