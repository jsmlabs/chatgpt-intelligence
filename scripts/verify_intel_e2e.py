#!/usr/bin/env python3
"""Validate twelve /INTEL fresh-chat acceptance records before release.

This checks structural consistency, not whether the ChatGPT observations
or linked evidence are genuine. Independent review remains mandatory.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

REQUIRED_CASES = {f"E2E-{index:02d}" for index in range(1, 13)}
VALID_RESULTS = {"passed", "failed", "blocked", "not-run"}
SHA40 = re.compile(r"[0-9a-fA-F]{40}\Z")


def _date_valid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _evidence_valid(value: object, root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme:
        return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password
    # Evidence paths are repository-relative and must exist. Do not allow
    # traversal, absolute paths or fragments masquerading as paths.
    if value.startswith(("/", "\\")) or parsed.query or parsed.fragment:
        return False
    target = (root / value).resolve()
    return target.is_relative_to(root.resolve()) and target.is_file()


def validate(path: Path, require_passed: bool = True) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError("schema_version must be 1")
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
            if not _date_valid(case.get("tested_on")):
                issues.append(f"{cid}: invalid or missing tested_on ISO date")
            if not isinstance(case.get("surface"), str) or not case["surface"].strip():
                issues.append(f"{cid}: passed but surface is missing")
            revision = case.get("source_revision")
            if not isinstance(revision, str) or not SHA40.fullmatch(revision):
                issues.append(f"{cid}: source_revision must be a full 40-character commit SHA")
            if not _evidence_valid(case.get("evidence"), path.parent.parent):
                issues.append(f"{cid}: evidence must be an existing repository-relative file or HTTPS URL")
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
