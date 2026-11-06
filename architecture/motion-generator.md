---
title: G3.1 GIF and Motion Generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G3.1 - GIF & Motion Generator

## Implemented capability

The dependency-free local motion runtime supports **JSON storyboards**
and **real animated GIF89a** files. It is an intentionally narrow,
offline, deterministic renderer for abstract geometric animation, not an
AI text-to-video model or general-purpose visual-effects engine.

- Motion families: `pulse`, `orbit`, `bounce`.
- Canvas: width and height each 64 to 256 pixels.
- Frames: 2 to 12; default 8.
- Frame delay: 50 to 1000 milliseconds, in 10ms increments.
- Loop count: `0` for infinite looping, `1..20` for finite repeat counts.
- Palette: G2.3 `graphite`, `ocean`, `plum`, `forest` presets;
  optional validated six-digit hex accent.
- Max GIF output: 2,000,000 bytes. No files downloaded; no additional
  Python packages; no remote or paid provider.

The JSON storyboard includes a complete ordered frame plan, canvas,
palette, timestamps, phase values, motion family and loop semantics.
The corresponding GIF is made of locally rendered indexed frames, with
a four-entry global color table, GIF89a graphic-control delays and
NETSCAPE2.0 loop extension. A simple deliberately low-compression
LZW stream is used for independently verifiable decoding.

The motion is **procedural geometric animation**. The objective is
recorded in the storyboard, not semantically translated into imagery.
Users must not interpret generated GIFs as arbitrary image/video
generation or as guaranteed representations of the objective.

## Usage on Windows

In the project directory:

```powershell
# Editable storyboard with exact frame sequence
python -m generators gif --objective "Loading indicator" --motion orbit --frames 8 --frame-duration-ms 120 --loop 0 --format json --authorize-create

# Export actual animated GIF (use an existing output directory)
python -m generators gif --objective "Loading indicator" --motion orbit --width 128 --height 128 --frames 8 --frame-duration-ms 120 --loop 0 --format gif --authorize-create --export-root . --filename loading-indicator.gif
```

The CLI requires a destination for binary GIF output; it does not write
raw image bytes to the terminal. Prefer an export directory outside the
public Git repository. JSON can be printed to standard output or saved
with exclusive export. Existing destination files are never overwritten.

## MCP

The additive `generate_motion` tool takes the same bounded parameters.
For `format=json`, it returns storyboard text. For `format=gif`, it
returns an MCP content block with `mimeType: image/gif` and Base64
image bytes. It always reports in-memory output as **not file-exported**.
Client support for displaying animated GIFs is host-dependent and must
be verified separately.

The standard host now advertises **13** tools (**14** with separately
enabled ComfyUI inference). The caller needs trusted process-level
`--allow-create` permission; request text cannot grant it.

## Verification and acceptance boundaries

The renderer generates the full binary GIF and validates it before
returning success. Its format-specific verifier checks GIF89a screen
and palette shape, Netscape loop metadata, every frame descriptor,
graphic-control delay, image subblocks, per-pixel LZW codes, exact
decoded pixel count, and absence of trailing data. The output is
SHA-256 hashed; an exported file is read back before reporting its
verified reference in the artifact manifest.

Tests include three motion families, deterministic results, repeatable
loops, timing and frame corruption rejection, invalid parameters,
denied permissions, path traversal attempts, exclusive export,
CLI invocation and MCP JSON/image tool responses.

This is **structural and format validation**, not human perception
or editorial review. External animation players and browser display
have not been independently attested. Smoothness, aesthetics,
photorealism, meaningful scene interpretation, copyright/rights
assessment and accessibility (including seizure-sensitive flashing)
require separate review. No MP4/video, arbitrary imported frame
sequence or source-driven animation exists in G3.1.

[Generator roadmap](../GENERATOR-ROADMAP.md) |
[IMAGE generator](image-generator.md) |
[BRAND generator](brand-generator.md)
