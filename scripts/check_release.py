#!/usr/bin/env python3
"""Fail closed on incomplete ChatGPT Intelligence release gates.

Usage:
    python scripts/check_release.py --root .
    python scripts/check_release.py --root . --report-only

The evidence file is a human-reviewed attestation, not proof that a
ChatGPT client, visual asset, or independent review actually passed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

TAGLINE = (
    "Research, concepts, prompts, knowledge, memory, context engineering, "
    "and intelligent UI principles for high-quality, personalized ChatGPT experiences."
)
DOMAINS = (
    "research", "concepts", "prompts", "knowledge", "memory",
    "context-engineering", "intelligent-ui",
)
REQUIRED_GATES = (
    "fresh_chat_intel",
    "intelligent_ui",
    "brand_visual_review",
    "independent_editorial_privacy_review",
)


def check(root: Path) -> list[str]:
    root = root.resolve()
    failures: list[str] = []
    readme = root / "README.md"
    if not readme.is_file() or TAGLINE not in readme.read_text(encoding="utf-8"):
        failures.append("canonical README tagline missing or changed")
    for domain in DOMAINS:
        if not (root / domain / "README.md").is_file():
            failures.append(f"missing domain index: {domain}/README.md")

    brand = root / "branding" / "v1.4"
    manifest_path = brand / "MANIFEST.json"
    if not manifest_path.is_file():
        failures.append("branding/v1.4/MANIFEST.json not published")
    else:
        try:
            import importlib.util
            script = root / "scripts" / "verify_branding.py"
            spec = importlib.util.spec_from_file_location("verify_branding", script)
            if spec is None or spec.loader is None:
                raise ValueError("branding verifier not loadable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if module.verify(brand) != 0:
                failures.append("branding manifest verification failed")
        except (OSError, ValueError, ImportError, AttributeError, KeyError, TypeError) as exc:
            failures.append(f"branding verifier unavailable: {exc}")

    evidence_file = root / "quality" / "release-evidence.json"
    try:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
        if not isinstance(evidence, dict):
            raise ValueError("evidence must be an object")
    except (OSError, ValueError) as exc:
        failures.append(f"release-evidence.json missing or invalid: {exc}")
        evidence = {}

    for gate in REQUIRED_GATES:
        item = evidence.get(gate)
        if not isinstance(item, dict):
            failures.append(f"{gate}: missing attestation")
            continue
        if item.get("status") != "passed":
            failures.append(f"{gate}: not passed")
        elif not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            failures.append(f"{gate}: passed but missing supporting evidence reference")

    intel = evidence.get("fresh_chat_intel")
    if isinstance(intel, dict) and intel.get("status") == "passed":
        try:
            import importlib.util
            verifier = root / "scripts" / "verify_intel_e2e.py"
            spec = importlib.util.spec_from_file_location("verify_intel_e2e", verifier)
            if spec is None or spec.loader is None:
                raise ValueError("E2E verifier not loadable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            failures.extend(
                f"fresh_chat_intel case evidence: {issue}"
                for issue in module.validate(root / "quality/intel-e2e-results.json")
            )
        except (OSError, ValueError, ImportError, AttributeError, TypeError) as exc:
            failures.append(f"fresh_chat_intel per-case verification unavailable: {exc}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    failures = check(args.root)
    for issue in failures:
        print("BLOCKED:", issue)
    if failures:
        print(f"Release readiness: BLOCKED ({len(failures)} unmet conditions)")
        return 0 if args.report_only else 1
    print("Release readiness: structural gates satisfied; human evidence review still required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
