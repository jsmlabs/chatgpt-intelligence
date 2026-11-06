"""Unified offline-first local CLI. ChatGPT /INTEL is a separate convention."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
VERSION = "0.1.0"
COMMANDS = {
    "help": "Show commands and examples",
    "version": "Show CLI version",
    "generate": "Run an existing deterministic generator",
    "config": "Show or set local preferences",
    "providers": "Inspect optional providers (no connections)",
    "doctor": "Check local prerequisites without changing anything",
    "status": "Show installed local capabilities",
    "setup": "Show safe installation steps",
    "start": "Start the optional Windows tunnel in the foreground",
    "test": "Run the Python unit test suite",
    "check": "Run documentation checks and unit tests",
    "verify": "Run existing local MCP verification",
    "dev": "Show developer shortcuts",
}
MESSAGES = {
    "en": {"title": "ChatGPT Intelligence", "choose": "Select a command (0 to exit): ",
           "invalid": "Invalid selection.", "goodbye": "Exit.", "saved": "Language saved.",
           "language": "Language", "optional": "Optional", "missing": "Missing",
           "available": "Available", "not_available": "Not available",
           "setup": "Install Python 3.12+ and use intel generate --help. Tunnel and models are optional.",
           "dev": "Developer shortcuts: intel test | intel check | intel verify",
           "unsupported": "This command requires Windows PowerShell and a configured tunnel."},
    "de": {"title": "ChatGPT Intelligence", "choose": "Befehl wählen (0 zum Beenden): ",
           "invalid": "Ungültige Auswahl.", "goodbye": "Beenden.", "saved": "Sprache gespeichert.",
           "language": "Sprache", "optional": "Optional", "missing": "Fehlt",
           "available": "Verfügbar", "not_available": "Nicht verfügbar",
           "setup": "Python 3.12+ installieren und intel generate --help verwenden. Tunnel und Modelle sind optional.",
           "dev": "Entwicklerbefehle: intel test | intel check | intel verify",
           "unsupported": "Dieser Befehl benötigt Windows PowerShell und einen konfigurierten Tunnel."},
}
COLORS = {"info": "36", "pass": "32", "warn": "33", "fail": "31", "muted": "90"}

def config_path() -> Path:
    base = os.environ.get("INTEL_CONFIG_HOME")
    if base:
        return Path(base).expanduser() / "config.json"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "ChatGPTIntelligence" / "config.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "chatgpt-intelligence" / "config.json"

def read_language() -> str:
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
        return data.get("language", "en") if data.get("language") in MESSAGES else "en"
    except (OSError, ValueError, TypeError, AttributeError):
        return "en"

def save_language(language: str) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never follow or overwrite an existing symlink as a config destination.
    if path.is_symlink():
        raise OSError("Refusing to write through a configuration symlink")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=".intel-", suffix=".tmp", delete=False) as file:
        temp = Path(file.name)
        json.dump({"language": language}, file, ensure_ascii=False)
        file.write("\n")
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

class Console:
    def __init__(self, *, language: str, json_mode: bool, quiet: bool, no_color: bool):
        self.language, self.json_mode, self.quiet = language, json_mode, quiet
        self.color = not (json_mode or no_color or os.environ.get("NO_COLOR") is not None
                          or os.environ.get("TERM") == "dumb" or not sys.stdout.isatty())
        if os.name == "nt" and not (os.environ.get("WT_SESSION") or os.environ.get("ANSICON")
                                    or os.environ.get("ConEmuANSI") == "ON"):
            self.color = False

    def tr(self, key: str) -> str:
        return MESSAGES[self.language].get(key, MESSAGES["en"].get(key, key))

    def emit(self, text: str, kind: str = "info") -> None:
        if self.quiet or self.json_mode:
            return
        prefix = {"pass": "[PASS]", "warn": "[WARN]", "fail": "[FAIL]",
                  "skip": "[SKIP]", "blocked": "[BLOCKED]"}.get(kind, "")
        line = (prefix + " " if prefix else "") + text
        color = COLORS.get(kind, "36")
        print(f"\033[{color}m{line}\033[0m" if self.color else line)

    def output(self, data: dict) -> None:
        if self.json_mode:
            print(json.dumps(data, ensure_ascii=False, sort_keys=True))
        elif not self.quiet:
            for key, value in data.items():
                self.emit(f"{key}: {value}")

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="intel", description="Offline-first ChatGPT Intelligence local CLI",
                                epilog="Examples: intel generate prompt --objective 'Draft a checklist' --authorize-create; intel config language de")
    p.add_argument("--json", action="store_true", help="Machine-readable output for built-in inspection commands")
    p.add_argument("--quiet", action="store_true", help="Suppress informational text")
    p.add_argument("--verbose", action="store_true", help="Show command details")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p.add_argument("--non-interactive", action="store_true", help="Never prompt")
    p.add_argument("command", nargs="?", choices=tuple(COMMANDS))
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    return p

def inspect(command: str) -> dict:
    if command == "version":
        return {"cli_version": VERSION}
    if command == "providers":
        return {"template": "available (offline)", "ollama-local": "optional (not contacted)",
                "chatgpt-host": "host required", "openai-api": "optional, explicit authorization required",
                "comfyui": "optional (not contacted)"}
    if command == "status":
        return {"local_generator": "available", "mcp_server": "python -m generators.mcp_server",
                "tunnel": "optional; not started", "language": read_language()}
    return {"python": sys.version.split()[0], "generator_package": (ROOT / "generators" / "__main__.py").is_file(),
            "powershell": bool(shutil.which("powershell.exe") or shutil.which("pwsh")),
            "tunnel_launcher": (ROOT / "scripts" / "intel.ps1").is_file(),
            "mcp_server": (ROOT / "generators" / "mcp_server.py").is_file(),
            "configured_language": read_language()}

def run_script(script: str, *args: str) -> int:
    path = ROOT / script
    if not path.is_file():
        print(f"[BLOCKED] Required script missing: {script}", file=sys.stderr)
        return 3
    return subprocess.run([sys.executable, str(path), *args], cwd=str(ROOT), check=False).returncode

def menu(console: Console) -> int:
    if not sys.stdin.isatty():
        print("[BLOCKED] No interactive terminal. Run intel help.", file=sys.stderr)
        return 2
    choices = ("generate", "status", "doctor", "providers", "config", "test", "help", "start")
    while True:
        console.emit(console.tr("title"))
        for i, command in enumerate(choices, 1):
            console.emit(f"{i:>2}. {command:10} {COMMANDS[command]}")
        console.emit(" 0. Exit")
        try:
            choice = input(console.tr("choose")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice == "0":
            return 0
        if not choice.isdigit() or not 1 <= int(choice) <= len(choices):
            console.emit(console.tr("invalid"), "warn")
            continue
        selected = choices[int(choice) - 1]
        if selected == "generate":
            console.emit("Use: intel generate prompt --objective \"...\" --authorize-create")
            continue
        if selected == "config":
            console.emit(f"{console.tr('language')}: {read_language()} (intel config language de)")
            continue
        code = dispatch(selected, [], console)
        if code:
            console.emit(f"Exit code: {code}", "warn")

def dispatch(command: str, args: list[str], console: Console) -> int:
    if command == "help":
        for name, description in COMMANDS.items():
            console.emit(f"{name:10} {description}")
        console.emit("Legacy: python -m generators <type> ... | scripts/intel.ps1 -Action Start")
        return 0
    if command == "generate":
        from generators.__main__ import main as generate_main
        return generate_main(args)  # Preserve original parser, formats, permission gates and streams.
    if command == "config":
        if args == ["language", "show"] or not args:
            console.output({"language": read_language()})
            return 0
        if len(args) == 2 and args[0] == "language" and args[1] in MESSAGES:
            try:
                save_language(args[1])
            except OSError as exc:
                print(f"[FAIL] Could not save language: {exc}", file=sys.stderr)
                return 3
            console.language = args[1]
            console.output({"language": args[1]})
            return 0
        print("[FAIL] Usage: intel config language {en|de|show}", file=sys.stderr)
        return 2
    if args:
        print(f"[FAIL] Unexpected arguments for {command}: {' '.join(args)}", file=sys.stderr)
        return 2
    if command in ("version", "providers", "status", "doctor"):
        console.output(inspect(command))
        return 0
    if command in ("setup", "dev"):
        console.emit(console.tr(command))
        return 0
    if command == "test":
        return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                              cwd=str(ROOT), check=False).returncode
    if command == "check":
        code = run_script("scripts/check_docs.py", "--root", ".")
        return code if code else dispatch("test", [], console)
    if command == "verify":
        return run_script("scripts/verify_host_mcp.py")
    if command == "start":
        executable = shutil.which("powershell.exe")
        if os.name != "nt" or not executable:
            print(f"[BLOCKED] {console.tr('unsupported')}", file=sys.stderr)
            return 3
        return subprocess.run([executable, "-NoProfile", "-File",
                               str(ROOT / "scripts" / "intel.ps1"), "-Action", "Start"],
                              cwd=str(ROOT), check=False).returncode
    return 2

def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    # Permit global flags before or after the command, without stealing generator-specific flags.
    p = parser()
    options = p.parse_args(raw)
    console = Console(language=read_language(), json_mode=options.json,
                      quiet=options.quiet, no_color=options.no_color)
    if options.command is None:
        return 2 if options.non_interactive else menu(console)
    if options.verbose and not options.quiet and not options.json:
        print(f"intel {options.command}", file=sys.stderr)
    return dispatch(options.command, options.arguments, console)

if __name__ == "__main__":
    raise SystemExit(main())
