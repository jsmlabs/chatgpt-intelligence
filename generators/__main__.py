"""Local G1 command-line entry point. Not a native ChatGPT command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .foundation import Authorization, Permission
from .text_runtime import TextRuntime
from .model_host import OpenAIResponsesHost
from .ollama_host import OllamaLocalHost
from .provider_router import ProviderRouter
from .capabilities import GENERATOR_NAMES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="INTEL local deterministic text generators")
    parser.add_argument("type", choices=GENERATOR_NAMES)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--audience", default="General audience")
    parser.add_argument("--diagram-kind", choices=["flowchart", "architecture"], default="flowchart")
    parser.add_argument("--diagram-direction", choices=["TB", "LR"], default="TB")
    parser.add_argument("--node", action="append", default=None,
                        help="Node: id|label|type (repeatable)")
    parser.add_argument("--edge", action="append", default=None,
                        help="Edge: source|target|label (repeatable)")
    parser.add_argument("--slide", action="append", default=None,
                        help="Slide as layout|title|body1|body2 (repeatable, max 12)")
    parser.add_argument("--motion", choices=["pulse", "orbit", "bounce"], default="pulse")
    parser.add_argument("--width", type=int, default=128)
    parser.add_argument("--height", type=int, default=128)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--frame-duration-ms", type=int, default=120)
    parser.add_argument("--loop", type=int, default=0)
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--palette", default="")
    parser.add_argument("--name", default=None, help="Brand display name (required for BRAND)")
    parser.add_argument("--value", action="append", default=[])
    parser.add_argument("--direction", choices=["orbit", "signal", "aperture"], default="orbit")
    parser.add_argument("--preset", choices=["graphite", "ocean", "plum", "forest"], default="graphite")
    parser.add_argument("--accent", default=None)
    parser.add_argument("--layout", choices=["dashboard", "landing", "form", "catalog"], default="dashboard")
    parser.add_argument("--responsive", choices=["mobile-first", "desktop-first"], default="mobile-first")
    parser.add_argument("--component", action="append", default=None)
    parser.add_argument("--style", default="")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--verify", action="append", default=[])
    parser.add_argument("--format", default=None)
    parser.add_argument("--mode", choices=["template", "model"], default="template")
    parser.add_argument("--provider", choices=["template", "ollama-local", "chatgpt-host",
                                               "openai-api"], default=None)
    parser.add_argument("--model-timeout", type=float, default=60.0)
    parser.add_argument("--model-max-output-tokens", type=int, default=4096)
    parser.add_argument("--authorize-external", action="store_true")
    parser.add_argument("--authorize-billable", action="store_true")
    parser.add_argument("--authorize-create", action="store_true",
                        help="Explicitly authorize local artifact creation by this CLI invocation")
    parser.add_argument("--export-root", type=Path)
    parser.add_argument("--filename")
    args = parser.parse_args(argv)
    granted = set()
    if args.authorize_create:
        granted.add(Permission.CREATE)
    if args.authorize_external:
        granted.add(Permission.EXTERNAL)
    if args.authorize_billable:
        granted.add(Permission.BILLABLE)
    if not 1 <= args.model_timeout <= 120 or not 128 <= args.model_max_output_tokens <= 8192:
        parser.error("Model timeout must be 1-120 seconds and tokens 128-8192")
    runtime = TextRuntime(provider_router=ProviderRouter(
        ollama_host=OllamaLocalHost(timeout=args.model_timeout,
                                    max_output_tokens=args.model_max_output_tokens),
        openai_host=OpenAIResponsesHost(timeout=args.model_timeout,
                                        max_output_tokens=args.model_max_output_tokens)))
    selected_runtime = runtime
    if args.type == "image":
        from .image_runtime import ImageRuntime
        selected_runtime = ImageRuntime()
    if args.type == "design":
        from .design_runtime import DesignRuntime
        selected_runtime = DesignRuntime()
    if args.type == "theme":
        from .theme_runtime import ThemeRuntime
        selected_runtime = ThemeRuntime()
    if args.type == "brand":
        from .brand_runtime import BrandRuntime
        selected_runtime = BrandRuntime()
    if args.type == "gif":
        from .motion_runtime import MotionRuntime
        selected_runtime = MotionRuntime()
    if args.type == "slides":
        from .slides_runtime import SlidesRuntime
        selected_runtime = SlidesRuntime()
    if args.type == "diagram":
        from .diagram_runtime import DiagramRuntime
        selected_runtime = DiagramRuntime()
    fmt = args.format if args.format is not None else ("json" if args.type in {"theme", "gif", "slides", "diagram"} else "markdown")
    request = {"objective": args.objective, "audience": args.audience,
               "style": args.style, "sources": args.source,
               "constraints": args.constraint, "verification": args.verify,
               "format": fmt}
    if args.type == "image":
        request.update(aspect_ratio=args.aspect_ratio, palette=args.palette)
    if args.type == "design":
        request.update(layout=args.layout, responsive=args.responsive)
        if args.component is not None:
            request["components"] = args.component
    if args.type == "theme":
        request = {"objective": args.objective, "format": fmt, "preset": args.preset}
        if args.accent is not None:
            request["accent"] = args.accent
    if args.type == "brand":
        request = {"objective": args.objective, "name": args.name or "",
                   "audience": args.audience, "style": args.style or "Minimal geometric",
                   "values": args.value, "preset": args.preset,
                   "direction": args.direction, "format": fmt}
        if args.accent is not None:
            request["accent"] = args.accent
    if args.type == "gif":
        request = {"objective": args.objective, "format": fmt, "motion": args.motion,
                   "width": args.width, "height": args.height, "frames": args.frames,
                   "frame_duration_ms": args.frame_duration_ms, "loop": args.loop,
                   "preset": args.preset}
        if args.accent is not None:
            request["accent"] = args.accent
        if fmt == "gif" and (args.export_root is None or args.filename is None):
            parser.error("GIF binary export requires --export-root and --filename")
    if args.type == "slides":
        request = {"objective": args.objective, "audience": args.audience,
                   "preset": args.preset, "format": fmt}
        if args.accent is not None:
            request["accent"] = args.accent
        if args.slide is not None:
            request["slides"] = []
            for spec in args.slide:
                items = spec.split("|")
                if len(items) < 2:
                    parser.error("Slide syntax: layout|title|body1|body2")
                request["slides"].append({"layout": items[0], "title": items[1],
                                          "body": items[2:]})
        if fmt == "pptx" and (args.export_root is None or args.filename is None):
            parser.error("PPTX binary export requires --export-root and --filename")
    if args.type == "diagram":
        request = {"objective": args.objective, "format": fmt,
                   "kind": args.diagram_kind, "direction": args.diagram_direction,
                   "preset": args.preset}
        if args.accent is not None:
            request["accent"] = args.accent
        if args.node is not None or args.edge is not None:
            if args.node is None:
                parser.error("--node is required when providing --edge")
            request["nodes"], request["edges"] = [], []
            for item in args.node:
                parts = item.split("|")
                if len(parts) not in (2, 3):
                    parser.error("Node syntax: id|label|type")
                request["nodes"].append({"id": parts[0], "label": parts[1],
                                          "type": parts[2] if len(parts) == 3 else "process"})
            for item in args.edge or []:
                parts = item.split("|")
                if len(parts) not in (2, 3):
                    parser.error("Edge syntax: source|target|label")
                request["edges"].append({"source": parts[0], "target": parts[1],
                                          "label": parts[2] if len(parts) == 3 else ""})
    result = selected_runtime.execute(
        "/INTEL GENERATE " + args.type.upper(),
        request=request,
        authorization=Authorization(frozenset(granted)),
        export_root=args.export_root, filename=args.filename, mode=args.mode,
        provider=args.provider,
    )
    if not result["ok"]:
        print(json.dumps(result["error"], sort_keys=True), file=sys.stderr)
        return 2
    manifest = result["manifest"]
    if isinstance(result["content"], bytes):
        print(json.dumps({"artifact_type": manifest.artifact_type,
                          "output_reference": manifest.content_reference,
                          "sha256": result["evidence"].get("file_sha256"),
                          "slide_count": result["evidence"].get("slide_count"),
                          "frame_count": result["evidence"].get("frame_count")}, sort_keys=True))
    else:
        print(result["content"], end="")
    print(json.dumps({"artifact_id": manifest.identifier, "state": manifest.state.value,
                      "version": manifest.version, "source_status": "unverified",
                      "output_reference": manifest.content_reference,
                      "evidence": result["evidence"]}, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
