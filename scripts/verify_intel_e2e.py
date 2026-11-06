#!/usr/bin/env python3
"""Validate the twelve per-case /INTEL fresh-chat evaluation records.

This validates record structure and completeness, not whether an observed
ChatGPT output or citation is authentic. Manual evidence review is required.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REQUIRED_CASES = {f"E2E-{index:02d}" for index in range(1, 13)}
VALID_RESULTS = {"passed", "failed", "blocked", "not-run"}


def validate(path: Path, require_passed: bool = True) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases = payload["cases"]
        if not isinstance(cases, list):
            raise ValueError("cases must be a list")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"invalid E2E results file: {exc}"]
    issues: list[str] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            issues.append("case entry must be an object")
            continue
        cid = case.get("case_id")
        if not isinstance(cid, str):
            issues.append("missing case_id")
            continue
        if cid in seen:
            issues.append(f"{cid}: duplicate")
        seen.add(cid)
        if cid not in REQUIRED_CASES:
            issues.append(f"{cid}: unknown case")
        status = case.get("result")
        if status not in VALID_RESULTS:
            issues.append(f"{cid}: invalid result")
        if require_passed and status != "passed":
            issues.append(f"{cid}: not passed")
        if status == "passed":
            for field in ("tested_on", "surface", "source_revision", "evidence"):
                value = case.get(field)
                if not isinstance(value, str) or not value.strip():
                    issues.append(f"{cid}: passed but {field} is missing")
    for cid in sorted(REQUIRED_CASES - seen):
        issues.append(f"{cid}: missing case")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path("quality/intel-e2e-results.json"))
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    issues = validate(args.file)
    for issue in issues:
        print("BLOCKED:", issue)
    print(f"INTEL fresh-chat E2E records: {'BLOCKED' if issues else 'STRUCTURALLY COMPLETE'}")
    return 0 if args.report_only or not issues else 1


if __name__ == "__main__":
    sys.exit(main())
