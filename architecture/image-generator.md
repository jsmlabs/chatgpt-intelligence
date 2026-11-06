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

## G2.1.2 - Local semantic image generation through ComfyUI

**Implemented adapter, live environment not yet verified.** A separately
installed local [ComfyUI](https://github.com/Comfy-Org/ComfyUI) server with a
locally available checkpoint is required. The adapter uses the official
[ComfyUI example workflow](https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/basic_api_example.py)
with fixed core nodes `CheckpointLoaderSimple`, `CLIPTextEncode`,
`EmptyLatentImage`, `KSampler`, `VAEDecode` and `SaveImage`, and
official `/prompt`, `/history/{prompt_id}`, `/view` HTTP endpoints
([official example](https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/websockets_api_example.py)).
The locally trusted graph is constructed from typed parameters; callers
cannot inject an arbitrary ComfyUI workflow, custom nodes, Partner API nodes,
URLs, headers or model credentials.

**Default: disabled.** No additional Python packages, model downloads,
remote model services or paid API calls are performed. The fixed endpoint is
`http://127.0.0.1:8188` only; redirects and environment proxies are
disabled. A locally configured `.safetensors` checkpoint filename must
match the installed-model list before the workflow is submitted.
The local inference grant is explicit and separate from the default CREATE
permission.

### Windows local CLI

Install ComfyUI and a compatible local **checkpoint** independently, using its
official installation instructions. Ensure that the checkpoint is loaded in
the local ComfyUI model list, the local server is reachable at
`127.0.0.1:8188`, and no paid/Partner nodes or remote services are present
in the trusted workflow. Ollama `gemma3:4b` is not a diffusion checkpoint
and cannot substitute for an image model.

```powershell
cd "C:\Users\jsmue\Desktop\Projects\chatgpt-intelligence"
$env:INTEL_COMFYUI_CHECKPOINT = "your-installed-checkpoint.safetensors"

# Check ComfyUI is running and checkpoint is installed
Invoke-RestMethod -Uri "http://127.0.0.1:8188/models/checkpoints"

# Single explicit local generation; output folder must exist
python -m generators.comfyui_image `
    --prompt "Cinematic mountain landscape at sunrise" `
    --negative-prompt "text, watermark" `
    --width 512 --height 512 --steps 20 --seed 7 `
    --authorize-create --authorize-local-inference `
    --export-root . --filename "intel-comfyui.png"
```

The CLI only writes an exclusive new `.png` file after an image passes
bounded PNG signature/chunk/CRC/dimension checks and file readback. It
returns the actual checkpoint name and ComfyUI prompt ID, but does not
claim subjective visual quality, image safety, source verification or human
approval. The decoder itself is not independently validated pixel-by-pixel;
do not confuse structural verification with editorial image review.

### Optional ChatGPT MCP tool

When a trusted operator explicitly starts the MCP host with
`--allow-create --allow-comfyui-image`, a **tenth** tool,
`generate_image_comfyui`, becomes discoverable. Without the startup flag
the default remains **nine** tools, and no ComfyUI call is authorized.
The flag does not grant broad EXTERNAL or BILLABLE permissions to other
generators. The MCP tool returns image bytes in an `image/png` content
block and bounded provenance, **not** a local file export. The same
running tunnel must be restarted and ChatGPT tools refreshed after
changing the profile's stdio command; do not enable this flag automatically.

The existing Windows `intel.cmd` start profile is intentionally unchanged.
Use direct CLI local generation until you explicitly opt into altering
that trusted MCP profile. Never put the runtime API key or model files in
the repository.

### Verification boundary and operational risks

- Synthetic tests mock the local ComfyUI API; CI cannot attest that your
  machine has ComfyUI, a checkpoint, sufficient VRAM, or a successfully
  rendered semantic image.
- One workflow is queued per authorized request. No automatic retries,
  model install, queue cancellation or billing fallback; on timeout a
  workflow may continue running in ComfyUI and should be inspected manually.
- A hostile or untrusted loopback service can return misleading results.
  Restrict ComfyUI to `127.0.0.1`, keep installed plugins and models trusted
  and inspect images, rights, text and privacy before using outputs.
- Only validated 8-bit RGB/RGBA non-interlaced PNG structures, max 1024x1024
  and 4 MiB, are accepted. Unsupported output fails with a typed error.
- No guarantee that an arbitrary semantic prompt follows its intent; the
  model, prompt, seed and actual image should be independently reviewed.

**Status:** ComfyUI adapter and MCP interface implemented; synthetic
CI tests required; live local model and ChatGPT E2E **not run**.

## Deferred: other semantic image providers

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

**Implementation status:** image production briefs, procedural abstract PNG
rendering and an opt-in ComfyUI semantic rendering adapter implemented.
Actual local checkpoint inference and ChatGPT MCP rendering must be verified
on a machine with ComfyUI installed. Do not label those live checks passed.
