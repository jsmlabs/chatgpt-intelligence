---
title: G2.1.3 local ComfyUI acceptance
status: proposed
version: 0.1.0
updated: 2026-11-06
classification: experimental
---

# G2.1.3 - Local ComfyUI installation and acceptance

This checklist is **not evidence that ComfyUI was installed or used on the
operator's Windows computer**. The G2.1.2 API adapter is implemented and
CI-tested with synthetic responses; a real checkpoint and GPU environment
are separate prerequisites.

## 1. Install and start ComfyUI

Use the [official ComfyUI installation instructions](https://docs.comfy.org/installation/overview)
to select the supported Windows installation method for your GPU.
Do not assume GPU vendor, driver, VRAM, Windows version compatibility or model
licence without inspecting the actual computer.

Start ComfyUI so its local API is available at `127.0.0.1:8188`.
The INTEL adapter uses a fixed graph of ComfyUI core nodes. It requires a
compatible `.safetensors` **checkpoint** loaded under ComfyUI's checkpoint
models. An Ollama text model is not interchangeable with a diffusion
checkpoint. Do not install untrusted custom nodes or choose Partner API /
cloud workflows for this local-only path.

Models can be large. Review model licence, intended use, available VRAM,
disk space, and source authenticity before any download. The repository
deliberately does not choose or download a model without those facts.

## 2. Update and inspect before generating

In Windows PowerShell 5.1:

```powershell
cd "$env:USERPROFILE\Desktop\Projects\chatgpt-intelligence"
git pull --ff-only origin main

# Read-only discovery; no workflow queued
Invoke-RestMethod -Uri "http://127.0.0.1:8188/models/checkpoints"

# Choose the exact filename returned by ComfyUI
$env:INTEL_COMFYUI_CHECKPOINT = "your-installed-checkpoint.safetensors"

# Preflight (does not create an image or write a file)
python -m scripts.verify_comfyui_live
```

Expected preflight: `status: READY`, `checkpoint_installed: true`,
`image_generated: false`, `paid_provider_invoked: false`.
If `status: BLOCKED`, inspect `reason`; do not interpret BLOCKED as
a successfully generated image. A missing checkpoint or unreachable local
API is an environment prerequisite, not a model test pass.

## 3. Explicit real-image acceptance

Run the following **only after** ComfyUI is running and you intentionally
authorize local model inference:

```powershell
python -m scripts.verify_comfyui_live `
    --authorize-local-inference `
    --output-dir . `
    --filename intel-comfyui-live.png `
    --prompt "A luminous blue glass sphere on a dark studio background" `
    --width 512 --height 512 --steps 12 --seed 7
```

Exactly one workflow is submitted by this invocation (without automatic
generation retries). It may require meaningful CPU/GPU time and VRAM.
The output file must not already exist; exclusive export refuses overwrites.
If ComfyUI times out, the queued job may continue running in ComfyUI;
check its local queue before repeating.

Expected output after a real run:

- `status: PASSED`, `provider: comfyui-local`.
- `image_generated: true`, `image_verified: true`, `file_verified: true`.
- `prompt_id`, `sha256`, `dimensions`, `checkpoint`, `output_file`.
- `human_review: not_run` and `source_verification: not_run`.

**Validation scope:** PNG structural checks, hash equality and local file
readback. The verifier cannot prove prompt fidelity, copyright compliance,
aesthetic quality, GPU identity or independent source verification. Open the
result and inspect it separately.

## 4. Optional ChatGPT plugin acceptance

Only after passing the local model test and reviewing operator permissions,
a trusted operator may modify the existing private tunnel profile's **stdio**
command to:

```powershell
python -m generators.mcp_server --allow-create --allow-comfyui-image
```

Do not add `--allow-billable`; the opt-in image tool needs local ComfyUI,
not an OpenAI Responses API entitlement. The default profile should remain
unchanged until the operator explicitly chooses to enable this tool.
Restart the existing tunnel using `intel.cmd` and refresh the installed
ChatGPT Intelligence plugin's tool list. The tenth tool should then appear
as `generate_image_comfyui`.

Perform a client-initiated image generation, confirm the returned MCP
`image/png` content and bounded provenance, and inspect the image.
This step is **not completed by CI or by running the local verifier**.
No private runtime key, complete prompt text or private generated image
is required in public release evidence.

## Exit criteria and evidence

| Gate | Evidence required | Current status |
| --- | --- | --- |
| Adapter and synthetic protocol tests | Exact main commit with green CI | Automated |
| ComfyUI and checkpoint available | Local read-only preflight READY | Not run |
| Real model inference | CLI PASSED with output hash and file inspection | Not run |
| ChatGPT model-image tool | Enabled private tunnel, tool discovery and real call | Not run |
| Privacy, rights and content review | Recorded independent review | Not run |

G2.1.3 and full G2 / release certification remain open until the
operator's real environment provides these results.
