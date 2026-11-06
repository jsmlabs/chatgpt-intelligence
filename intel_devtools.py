"""Bounded, offline-first CLI developer diagnostics; delegates existing checks.

No hidden network calls, process termination, arbitrary cleanup, or permission grants.
Structured report contract: schema_version, command, profile, status, exit_code, checks.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from intel_config import ConfigError, effective, issues
import intel_lifecycle

ROOT = Path(__file__).resolve().parent
REPORT_VERSION = 1
EXIT_PASS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_BLOCKED = 3
MAX_LOG_BYTES = 65536
MAX_LOG_LINES = 100
ALLOWED_LOG_SUFFIXES = frozenset({".log", ".txt"})
CHECK_PROFILES = ("docs", "tests", "all", "safety")
VERIFY_PROFILES = ("mcp", "release")
DOCTOR_PROFILES = ("basic", "full")

# Redact credentials, not all diagnostics. Never emit an unredacted external
# command output from the structured runner.
REDACTIONS = (
    (re.compile(r"(?i)\b(?:bearer)\s+[a-z0-9._~+/-]+(?:=+)?"), "Bearer [REDACTED]"),
    (re.compile(r"\b(?:sk-(?:proj-|test-)?[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{24,}|xoxb-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16})\b"), "[REDACTED]"),
    (re.compile(r'(?i)(\b(?:api[_-]?key|access[_-]?token|secret|password|credential|authorization)\b\s*[:=]\s*)(?:"[^"\r\n]*"|\'[^\'\r\n]*\'|[^\s,;}]+)'), r"\1[REDACTED]"),
)


def redact(value: str) -> str:
    for pattern, replacement in REDACTIONS:
        value = pattern.sub(replacement, value)
    return value


def result(command: str, profile: str, checks: list[dict[str, object]],
           *, status: str | None = None, exit_code: int | None = None) -> dict[str, object]:
    if exit_code is None:
        exit_code = (EXIT_BLOCKED if any(c["status"] == "blocked" for c in checks)
                     else EXIT_FAILURE if any(c["status"] == "failed" for c in checks)
                     else EXIT_PASS)
    if status is None:
        status = "blocked" if exit_code == EXIT_BLOCKED else "failed" if exit_code else "passed"
    return {"schema_version": REPORT_VERSION, "command": command, "profile": profile,
            "status": status, "exit_code": exit_code, "checks": checks}


def _item(name: str, status: str, detail: str) -> dict[str, str]:
    return {"id": name, "status": status, "detail": redact(detail)[:500]}


def doctor(profile: str = "basic") -> dict[str, object]:
    if profile not in DOCTOR_PROFILES:
        raise ValueError("Invalid doctor profile")
    checks = [
        _item("python", "passed" if sys.version_info >= (3, 11) else "failed",
              "Python 3.11+ runtime"),
        _item("generators", "passed" if (ROOT / "generators" / "__main__.py").is_file() else "failed",
              "Local generator entrypoint"),
        _item("mcp", "passed" if (ROOT / "generators" / "mcp_server.py").is_file() else "failed",
              "Stdio MCP source (not a live host test)"),
    ]
    if profile == "full":
        try:
            problems = issues()
            checks.append(_item("config", "failed" if any(p["severity"] == "error" for p in problems)
                                else "passed", "Config schema valid; optional initialization"
                                if not problems else "; ".join(p["code"] for p in problems)))
        except (ConfigError, OSError):
            checks.append(_item("config", "blocked", "Configuration inaccessible; run intel config validate"))
        running = intel_lifecycle.inspect()
        state = str(running["state"])
        checks.append(_item("tunnel", "blocked" if state == "unverified" else "skipped",
                            "Managed runtime " + state + "; no remote connectivity check"))
        checks.append(_item("git", "passed" if shutil.which("git") else "skipped",
                            "Git executable available" if shutil.which("git") else "Git not installed"))
    return result("doctor", profile, checks)


def _run_check(name: str, argv: list[str], *, timeout: int = 90) -> dict[str, object]:
    # Trusted scripts already in this checkout; capture and redact stdout/stderr.
    try:
        p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return _item(name, "blocked", "Check could not start or timed out")
    # Never copy raw subprocess data into JSON or console. A diagnostic can
    # include user-supplied paths/credentials; only expose safe counts/state.
    return {**_item(name, "passed" if p.returncode == 0 else "failed",
                    f"Exit {p.returncode}; output captured and suppressed"),
            "process_exit_code": p.returncode}


def check(profile: str = "all") -> dict[str, object]:
    if profile not in CHECK_PROFILES:
        raise ValueError("Invalid check profile")
    steps = {
        "docs": ("docs", [sys.executable, "scripts/check_docs.py", "--root", "."]),
        "tests": ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
        "safety": ("safety", [sys.executable, "scripts/check_publication_safety.py", "--root", "."]),
    }
    names = ("docs", "tests") if profile == "all" else (profile,)
    checks = []
    for name in names:
        entry = steps[name]
        item = _run_check(*entry)
        checks.append(item)
        if item["status"] != "passed":
            break
    return result("check", profile, checks)


def verify(profile: str = "mcp", *, authorize_local_create: bool = False) -> dict[str, object]:
    if profile not in VERIFY_PROFILES:
        raise ValueError("Invalid verify profile")
    if profile == "mcp":
        if not authorize_local_create:
            return result("verify", profile, [_item("mcp", "blocked",
                          "Explicit --authorize-local-create required for synthetic MCP checks")])
        return result("verify", profile, [_run_check("mcp",
            [sys.executable, "scripts/verify_host_mcp.py", "--authorize-local-create"], timeout=30)])
    # Evaluate the actual release gate, without report-only masking.
    return result("verify", profile, [_run_check("release",
        [sys.executable, "scripts/check_release.py", "--root", "."])])


def clean() -> dict[str, object]:
    # Only preview known generated cache directory. Do not inspect or delete
    # arbitrary project files, stale PIDs, Git state, or user artifacts.
    target = ROOT / ".intel-cache"
    exists = target.exists() or target.is_symlink()
    return result("clean", "preview", [_item("cache", "skipped",
        "Unmanaged cache present; manual review required" if exists
        else "No managed cache to clean")], status="preview")


def update() -> dict[str, object]:
    if shutil.which("git") is None:
        return result("update", "offline", [_item("git", "blocked", "Git unavailable")])
    checks = [_item("network", "skipped", "No remote fetch; origin update status is not verified")]
    commands = (
        ("head", ["git", "rev-parse", "--verify", "HEAD"]),
        ("tracking", ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]),
        ("dirty", ["git", "status", "--porcelain", "--untracked-files=no"]),
    )
    results = {}
    for name, args in commands:
        try:
            p = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            checks.append(_item(name, "blocked", "Git inspection unavailable"))
            continue
        results[name] = p
        checks.append(_item(name, "passed" if p.returncode == 0 else "skipped",
                            ("Tracked changes detected" if p.stdout.strip() else "No tracked changes")
                            if name == "dirty" and p.returncode == 0 else
                            "Local repository metadata inspected" if p.returncode == 0 else
                            "Local metadata unavailable"))
    report = result("update", "offline", checks, status="inspection")
    report["remote_checked"] = False
    report["update_available"] = None
    report["working_tree_clean"] = (not results["dirty"].stdout.strip()
                                    if "dirty" in results and results["dirty"].returncode == 0 else None)
    return report


def logs(path: Path | None) -> dict[str, object]:
    if path is None:
        return result("logs", "local", [_item("source", "skipped",
               "No persistent managed runtime log exists; pass --file PATH for a local log")])
    # Explicit user-selected log file only. No link following or implicit search.
    if path.suffix.lower() not in ALLOWED_LOG_SUFFIXES or path.is_symlink():
        raise ValueError("Select a regular .log or .txt file, not a symbolic link")
    if not path.is_file():
        raise ValueError("Log file is missing or not regular")
    if path.stat().st_size > MAX_LOG_BYTES:
        raise ValueError("Log file exceeds 64 KiB limit")
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("Unable to read UTF-8 log") from exc
    selected = content.splitlines()[-MAX_LOG_LINES:]
    safe = [redact(line)[:2000] for line in selected]
    report = result("logs", "file", [_item("redaction", "passed",
                        f"{len(safe)} lines inspected; secrets masked on a best-effort basis")])
    report["lines"] = safe
    return report


def shortcuts() -> dict[str, object]:
    return {"schema_version": REPORT_VERSION, "commands": {
        "doctor": ["intel --json doctor full", "intel doctor basic"],
        "check": ["intel --json check docs", "intel --json check tests", "intel --json check safety"],
        "verify": ["intel --json verify mcp --authorize-local-create", "intel --json verify release"],
        "maintenance": ["intel --json clean", "intel --json update", "intel --json logs"],
    }}
