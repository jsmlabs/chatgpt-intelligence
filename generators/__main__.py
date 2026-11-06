"""Local G1 command-line entry point. Not a native ChatGPT command."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .foundation import Authorization, Permission
from .text_runtime import TextRuntime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="INTEL local deterministic text generators")
    parser.add_argument("type", choices=["prompt", "concept", "document"])
    parser.add_argument("--objective", required=True)
    parser.add_argument("--audience", default="General audience")
    parser.add_argument("--style", default="")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--verify", action="append", default=[])
    parser.add_argument("--format", default="markdown")
    parser.add_argument("--authorize-create", action="store_true",
                        help="Explicitly authorize local artifact creation by this CLI invocation")
    parser.add_argument("--export-root", type=Path)
    parser.add_argument("--filename")
    args = parser.parse_args(argv)
    result = TextRuntime().execute(
        "/INTEL GENERATE " + args.type.upper(),
        request={"objective": args.objective, "audience": args.audience,
                 "style": args.style, "sources": args.source,
                 "constraints": args.constraint, "verification": args.verify,
                 "format": args.format},
        authorization=Authorization(
            frozenset({Permission.CREATE}) if args.authorize_create else frozenset()),
        export_root=args.export_root, filename=args.filename,
    )
    if not result["ok"]:
        print(json.dumps(result["error"], sort_keys=True), file=sys.stderr)
        return 2
    manifest = result["manifest"]
    print(result["content"], end="")
    print(json.dumps({"artifact_id": manifest.identifier, "state": manifest.state.value,
                      "version": manifest.version, "source_status": "unverified",
                      "output_reference": manifest.content_reference,
                      "evidence": result["evidence"]}, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
