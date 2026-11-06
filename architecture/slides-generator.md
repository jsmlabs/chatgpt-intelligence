---
title: G3.2 SLIDES deterministic generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G3.2 - SLIDES Generator

## Implemented

The offline SLIDES generator produces an ordered JSON presentation
storyboard or a genuine, editable `PPTX` Open Packaging Convention /
PresentationML archive using **Python 3.11 standard library only**.

- Formats: `json` (`application/json`) and `pptx`
  (`application/vnd.openxmlformats-officedocument.presentationml.presentation`).
- Layout families: `title`, `section`, `bullets`, `two-column`.
- Maximum 12 slides, each with a title and at most 6 bounded body strings.
- Canvas: 16:9 widescreen, 12,192,000 × 6,858,000 English Metric Units.
- Themes: G2.3 `graphite`, `ocean`, `plum`, `forest`,
  optionally a custom `#RRGGBB` accent.
- All text stays editable in native PresentationML text boxes. The
  OOXML package includes an actual presentation part, master,
  layout, theme and individual slide parts.
- The output is a static layout. There are no charts, speaker notes,
  external images, custom fonts, AI-generated content, executable
  macros or connections to external providers.

The `objective` is required. The caller may supply a bounded `slides`
array of objects with `layout`, `title` and `body` fields.
When no explicit slides are provided, the deterministic default creates
three **placeholder** slides based on objective and audience. Defaults
do **not** claim to have researched the subject or verified facts.

## Export and verification

The local exporter refuses overwrites and path traversal, requires a
trusted pre-existing directory, writes and syncs bytes, re-reads the
output, and records SHA-256. Only an exported file with verified
readback advances its artifact manifest to `exported`.

The PPTX validator inspects ZIP CRC, the exact allowed OOXML part
inventory, bounded XML parts, XML parseability, slide count,
selected slide texts, and forbids relationships with external
targets. It does **not** claim to prove Microsoft PowerPoint or
LibreOffice compatibility, visual alignment, pagination, font
availability or layout overflow. Opening, rendering, accessibility,
contrast in an actual viewer and editorial checks remain separate
manual acceptance gates.

Maximum PPTX binary size is 250,000 bytes; this is an intentionally
limited first generator. No additional dependencies or implicit
billable, browser or network calls are introduced.

## Windows PowerShell CLI

```powershell
# Read the deterministic JSON storyboard
python -m generators slides --objective "Product roadmap" --audience "Engineering" --preset ocean --authorize-create

# Create an editable PPTX in an existing directory
python -m generators slides --objective "Product roadmap" --preset ocean --format pptx --slide "title|Product roadmap|Engineering" --slide "bullets|Next steps|Review scope|Build MVP|Verify release" --authorize-create --export-root . --filename product-roadmap.pptx
```

Prefer a dedicated output directory outside your public Git repository.
Each repeated `--slide` uses `layout|title|body1|body2`. Literal
pipe characters are not supported in the CLI shorthand; use the
structured MCP slide object format for more complex text.

## MCP

The additive `generate_slides` tool accepts `objective`, optional
`audience`, `preset`, `accent`, `format` and `slides`.
It requires the trusted `--allow-create` grant.

- `format=json`: in-memory storyboard text plus manifest and evidence.
- `format=pptx`: in-memory Base64 binary in
  `structuredContent.base64`, with MIME, verified package metadata,
  and **output_verified: false** (no file exported through MCP).

Default host discovery includes **14 tools**, or **15** with separately
enabled local ComfyUI inference. This does not attest that the host
UI can automatically download and open `structuredContent.base64`.
A live ChatGPT MCP call and an independent slide-viewer opening
remain unverified.

[Generator roadmap](../GENERATOR-ROADMAP.md) |
[THEME generator](theme-generator.md) |
[DESIGN generator](design-generator.md)
