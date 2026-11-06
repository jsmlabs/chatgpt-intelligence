---
title: G2.1 IMAGE production-brief generator
status: accepted
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G2.1 - IMAGE: implementation specification and limits

## Objective

Add a useful, offline-first IMAGE capability with deterministic and client
authored creative briefs, while preserving the 16-capability G0 registry,
permission boundaries and provenance. A *production brief* is not a rendered
bitmap. Rendering requires a separate image-capable host with independently
verified output; no such renderer is wired into the local Python runtime.

## Implemented contract

- Command: `/INTEL GENERATE IMAGE`, CLI `python -m generators image`.
- Input: `objective` (required); `audience`, `style`, `palette`,
  `aspect_ratio`, `sources`, `constraints`, `verification`.
- Aspect ratio enum: `1:1`, `3:2`, `2:3`, `4:3`, `3:4`, `16:9`, `9:16`.
- Output: `text/markdown` only, including a reusable visual prompt,
  creative direction, composition, variant directions, human review steps,
  and explicit limitations. No raster or image-data field.
- Permission: explicit trusted CREATE grant. No EXTERNAL or BILLABLE.
- Lifecycle: planned → ready → generating → validating → reviewed;
  optional exclusive file-verified `.md` export only.
- Provenance: `local-deterministic-template` or `client-submitted-draft`;
  client-generated text has `model_provider: not-attested`.
- Verification: bounded inputs and outputs, balanced Markdown fences,
  visible provenance, strict path handling and no silent fallback.
- Evidence: `image_generated: false`, `image_verified: false`.
  A reviewed or exported brief does not mean a visual asset exists.

## MCP contract

The server exposes `generate_image_brief` (offline deterministic output)
and `submit_image_brief` (validate user/client supplied Markdown). Both
declare bounded input JSON schema and preserve the existing process-level
CREATE permission. Existing six G1.9 MCP tools remain unchanged. No extra
cloud model invocation occurs.

## Local usage

```powershell
python -m generators image --objective "Premium campaign image" --aspect-ratio 16:9 --style "Editorial lighting" --palette "black and gold" --authorize-create
```

To write an editable Markdown brief to an already-existing directory:

```powershell
python -m generators image --objective "Campaign" --authorize-create --export-root . --filename image-brief.md
```

The export refuses to overwrite an existing file. The `--format png`,
`--provider openai-api` and `--provider ollama-local` paths are not
image-rendering implementations and must fail with explicit errors.

## G2.1.1 - Procedural raster rendering (implemented separately)

A pure Python local renderer now generates **actual PNG bytes** for decorative
abstract geometric artwork. It is not an AI image generation model and cannot
faithfully render arbitrary semantic subjects, labels, supplied photographs or
a detailed freeform image prompt. Input `objective` seeds repeatable geometry.
The optional `palette` accepts exactly three `#RRGGBB` colors and
`aspect_ratio` uses the existing G2.1 allowed values.

Local verified export (requires an existing output directory):

```powershell
python -m generators.image_render --objective "Abstract product artwork" --aspect-ratio 16:9 --palette "#101827,#9061f9,#e8dfff" --authorize-create --export-root . --filename artwork.png
```

The renderer uses no external calls, model API or additional dependencies.
A strict PNG header/chunk/CRC/pixel check, SHA-256 and readback after exclusive
file creation must succeed before reporting a verified file. It does not
overwrite existing files.

The additive `render_abstract_image` MCP tool responds with an actual
`image/png` content block, dimensions, checksum, and
`producer: local-procedural-geometry`. It does **not** write a file through
MCP, and `output_verified` remains false even when returned bytes pass
local validation. `semantic_prompt_followed` is always false.
This is a limited, explicit zero-cost local rendering capability, not
a verified connection to the ChatGPT image generator.

## Deferred: semantic AI image rendering

A future host image adapter must have verified tool capability, explicit
permission grants where needed, an authorized model/tool runtime,
documented size/format limits, actual image bytes or a provider-backed
verified artifact reference, and content/rights checks. Verify the
file or provider result before claiming `image_generated: true`,
recording image provenance or offering a download. No direct access to
the ChatGPT conversation image renderer is implied by an MCP connection.

## Acceptance criteria and evidence

Automated test scenarios cover: deterministic briefs, aspect ratio validation,
no implicit paid provider, denied CREATE, hostile input, bounded client
submission, ambiguous Markdown fences, exclusive Markdown export, local CLI,
and both MCP tools. CI is the source of truth for passing checks; a live
ChatGPT tool refresh and image-brief tool call remain separate G2.1
client-acceptance actions.

**Implementation status:** image production briefs implemented;
raster generation **not implemented**. Do not label the full image
generation product complete.
