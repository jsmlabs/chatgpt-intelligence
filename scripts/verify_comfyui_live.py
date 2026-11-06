"""G2.1.3 local ComfyUI acceptance.

Default mode is read-only preflight (no image generation). Live inference
requires explicit authorization and a supplied checkpoint. No credentials or
generated prompt/image contents are emitted in the JSON report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from generators.comfyui_image import ComfyUIHost, CHECKPOINT, export_comfy_image
from generators.foundation import Authorization, IntelError, Permission

DEFAULT_PROMPT = "A luminous blue glass sphere on a dark studio background"


def report(host: ComfyUIHost, *, authorize: bool = False,
           output_dir: Path | None = None, filename: str = "intel-comfyui-live.png",
           prompt: str = DEFAULT_PROMPT, steps: int = 12,
           width: int = 512, height: int = 512, seed: int = 7) -> dict:
    """Perform a read-only probe, optionally then queue exactly one workflow."""
    result = {
        "status": "BLOCKED",
        "mode": "live-generation" if authorize else "preflight",
        "provider": "comfyui-local",
        "endpoint": "http://127.0.0.1:8188",
        "model_configured": host.configured,
        "checkpoint_installed": False,
        "image_generated": False,
        "image_verified": False,
        "file_verified": False,
        "human_review": "not_run",
        "source_verification": "not_run",
        "paid_provider_invoked": False,
    }
    try:
        models = host._json("/models/checkpoints")
        if (not isinstance(models, list) or len(models) > 1024 or
                not all(isinstance(item, str) and len(item) < 256 for item in models)):
            raise IntelError("MODEL_RESPONSE_INVALID", "Invalid checkpoint inventory")
        result["checkpoint_count"] = len(models)
        if not host.configured:
            result["reason"] = "checkpoint_not_configured"
            return result
        result["checkpoint_installed"] = host.checkpoint in models
        if not result["checkpoint_installed"]:
            result["reason"] = "checkpoint_not_installed"
            return result
        if not authorize:
            result["status"] = "READY"
            result["reason"] = "inference_not_authorized"
            return result
        if output_dir is None:
            result["reason"] = "output_directory_required"
            return result
        if not output_dir.is_dir() or output_dir.is_symlink():
            result["reason"] = "invalid_output_directory"
            return result
        # The host performs its own checkpoint preflight, request limits and PNG checks.
        image = host.generate(prompt, authorization=Authorization(
            frozenset({Permission.CREATE, Permission.EXTERNAL})),
            width=width, height=height, steps=steps, seed=seed)
        result["image_generated"] = True
        result["image_verified"] = True
        result["prompt_id"] = image.prompt_id
        result["dimensions"] = [image.width, image.height]
        result["sha256"] = image.sha256
        result["checkpoint"] = image.checkpoint
        path = export_comfy_image(image, output_dir, filename)
        result["file_verified"] = True
        result["output_file"] = path
        result["status"] = "PASSED"
        return result
    except IntelError as exc:
        result["reason"] = exc.code
        # A timed-out or failed queue attempt might have been executed remotely.
        if authorize:
            result["inference_may_still_be_running"] = True
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local ComfyUI or explicitly test one real render")
    parser.add_argument("--checkpoint", default=None,
                        help="Installed local .safetensors filename (or INTEL_COMFYUI_CHECKPOINT)")
    parser.add_argument("--authorize-local-inference", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--filename", default="intel-comfyui-live.png")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args(argv)
    try:
        host = ComfyUIHost(checkpoint=args.checkpoint, timeout=args.timeout)
    except (TypeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": "invalid_configuration"}, sort_keys=True))
        return 2
    data = report(host, authorize=args.authorize_local_inference,
                  output_dir=args.output_dir, filename=args.filename,
                  prompt=args.prompt, steps=args.steps, width=args.width,
                  height=args.height, seed=args.seed)
    print(json.dumps(data, sort_keys=True))
    return 0 if data["status"] in ("READY", "PASSED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
