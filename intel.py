"""Unified offline-first local CLI, separate from the ChatGPT /INTEL convention."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from intel_console import Console, read_key
from intel_locales import CATALOGS, tr

ROOT = Path(__file__).resolve().parent
VERSION = "0.1.0"
COMMANDS = ("help", "version", "generate", "config", "providers", "doctor", "status",
            "setup", "start", "test", "check", "verify", "dev")
INSPECTION = frozenset(("help", "version", "config", "providers", "doctor", "status"))


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
        return data.get("language", "en") if data.get("language") in CATALOGS else "en"
    except (OSError, ValueError, TypeError, AttributeError):
        return "en"


def save_language(language: str) -> None:
    if language not in CATALOGS:
        raise ValueError("Unsupported language")
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
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


def parser(language: str | None = None) -> argparse.ArgumentParser:
    lang = language or read_language()
    p = argparse.ArgumentParser(prog="intel", description=tr(lang, "parser_desc"),
                                epilog=tr(lang, "parser_epilog"))
    p.add_argument("--json", action="store_true", help=tr(lang, "opt_json"))
    p.add_argument("--quiet", action="store_true", help=tr(lang, "opt_quiet"))
    p.add_argument("--verbose", action="store_true", help=tr(lang, "opt_verbose"))
    p.add_argument("--no-color", action="store_true", help=tr(lang, "opt_no_color"))
    p.add_argument("--non-interactive", action="store_true", help=tr(lang, "opt_noninteractive"))
    p.add_argument("command", nargs="?", choices=COMMANDS)
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    return p


def inspect(command: str) -> dict[str, object]:
    if command == "version":
        return {"cli_version": VERSION}
    if command == "providers":
        return {"template":"offline","ollama-local":"not_contacted",
                "chatgpt-host":"host_required","openai-api":"explicit_grant","comfyui":"not_contacted"}
    if command == "status":
        return {"local_generator":(ROOT / "generators" / "__main__.py").is_file(),
                "mcp_server":(ROOT / "generators" / "mcp_server.py").is_file(),
                "tunnel":"not_checked","language":read_language()}
    return {"python":sys.version.split()[0],
            "generator_package":(ROOT / "generators" / "__main__.py").is_file(),
            "powershell":bool(shutil.which("powershell.exe") or shutil.which("pwsh")),
            "tunnel_launcher":(ROOT / "scripts" / "intel.ps1").is_file(),
            "mcp_server":(ROOT / "generators" / "mcp_server.py").is_file(),
            "configured_language":read_language()}


def run_script(script: str, console: Console, *args: str) -> int:
    path = ROOT / script
    if not path.is_file():
        console.error(console.tr("missing_script", script=script), "blocked")
        return 3
    return subprocess.run([sys.executable, str(path), *args], cwd=str(ROOT), check=False).returncode


def choose_menu(console: Console, options: tuple[str, ...]) -> str | None:
    descriptions = {name:console.tr("desc." + name) for name in options}
    use_arrows = console.color and sys.stdin.isatty()
    if use_arrows:
        current = 0
        console.menu(options, descriptions, current)
        while True:
            key = read_key()
            if key in ("exit", "q", "Q", "0"):
                return None
            if key == "up":
                current = (current - 1) % len(options)
            elif key == "down":
                current = (current + 1) % len(options)
            elif key == "enter":
                return options[current]
            elif key.isdigit() and 1 <= int(key) <= len(options):
                return options[int(key)-1]
            else:
                continue
            console.menu(options, descriptions, current)
    console.menu(options, descriptions)
    try:
        answer = console.ask(console.tr("choose")).strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if answer in ("0", "00", "q", "Q"):
        return None
    if answer.isdigit() and 1 <= int(answer) <= len(options):
        return options[int(answer)-1]
    console.emit(console.tr("invalid"), "warn")
    return ""


def interactive_generate(console: Console) -> int:
    try:
        kind = console.ask(console.tr("menu_type")).strip().lower()
        if kind not in {"prompt", "concept", "document"}:
            console.emit(console.tr("menu_invalid_type"), "warn")
            return 2
        objective = console.ask(console.tr("menu_objective")).strip()
        if not objective:
            console.emit(console.tr("menu_empty"), "warn")
            return 2
        answer = console.ask(console.tr("menu_grant")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.emit(console.tr("menu_cancelled"), "skip")
        return 2
    if answer not in ("y", "yes", "j", "ja"):
        console.emit(console.tr("menu_cancelled"), "skip")
        return 2
    return dispatch("generate", [kind, "--objective", objective, "--authorize-create"], console)


def interactive_config(console: Console) -> int:
    try:
        choice = console.ask(console.tr("select_language")).strip()
    except (EOFError, KeyboardInterrupt):
        return 0
    if choice == "0":
        return 0
    return dispatch("config", ["language", {"1":"en", "2":"de"}.get(choice, "")], console)


def menu(console: Console) -> int:
    if not sys.stdin.isatty():
        console.error(console.tr("not_tty"), "blocked")
        return 2
    options = ("generate", "status", "doctor", "providers", "config", "test", "help", "start")
    while True:
        selected = choose_menu(console, options)
        if selected is None:
            return 0
        if selected == "":
            continue
        if selected == "generate":
            code = interactive_generate(console)
        elif selected == "config":
            code = interactive_config(console)
        else:
            code = dispatch(selected, [], console)
        if code:
            console.emit(f"{console.tr('exit_code')}: {code}", "warn")


def dispatch(command: str, args: list[str], console: Console) -> int:
    if command == "help":
        if args:
            console.error(console.tr("unexpected", command=command, args=" ".join(args)))
            return 2
        if console.json_mode:
            console.report({"commands":{name:tr("en", "desc." + name) for name in COMMANDS}})
        else:
            console.table([(name, console.tr("desc." + name), "info") for name in COMMANDS],
                          console.tr("commands"))
            console.emit(console.tr("flags"), "muted")
            console.emit(console.tr("legacy"), "muted")
        return 0
    if command == "generate":
        from generators.__main__ import main as generate_main
        return generate_main(args)  # Preserve original formats, permissions and streams.
    if command == "config":
        if args == ["language", "show"] or not args:
            console.report({"language":read_language()})
            return 0
        if len(args) == 2 and args[0] == "language" and args[1] in CATALOGS:
            try:
                save_language(args[1])
            except OSError as exc:
                console.error(console.tr("save_failed", error=exc))
                return 3
            console.language = args[1]
            console.report({"language":args[1]})
            return 0
        console.error(console.tr("usage_language"))
        return 2
    if args:
        console.error(console.tr("unexpected", command=command, args=" ".join(args)))
        return 2
    if command in ("version","providers","status","doctor"):
        console.report(inspect(command), console.tr(command))
        return 0
    if command in ("setup","dev"):
        console.emit(console.tr(command + "_text"))
        return 0
    if command == "test":
        return subprocess.run([sys.executable,"-m","unittest","discover","-s","tests"],
                              cwd=str(ROOT),check=False).returncode
    if command == "check":
        code = run_script("scripts/check_docs.py",console,"--root",".")
        return code if code else dispatch("test",[],console)
    if command == "verify":
        return run_script("scripts/verify_host_mcp.py",console)
    if command == "start":
        executable = shutil.which("powershell.exe")
        if os.name != "nt" or not executable:
            console.error(console.tr("unsupported"),"blocked")
            return 3
        return subprocess.run([executable,"-NoProfile","-File",
                               str(ROOT / "scripts" / "intel.ps1"),"-Action","Start"],
                              cwd=str(ROOT),check=False).returncode
    return 2


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(sys.argv[1:] if argv is None else argv)
    console = Console(language=read_language(),json_mode=args.json,
                      quiet=args.quiet,no_color=args.no_color)
    if args.command is None:
        if args.non_interactive:
            console.error(console.tr("no_command"),"blocked")
            return 2
        if args.json:
            console.error(console.tr("not_tty"),"blocked")
            return 2
        return menu(console)
    if args.json and args.command not in INSPECTION:
        console.error(console.tr("json_unsupported"))
        return 2
    if args.quiet and args.command in ("generate","test","check","verify","start"):
        console.error(console.tr("quiet_unsupported"))
        return 2
    if args.verbose and not args.quiet and not args.json:
        print(f"intel {args.command}", file=sys.stderr)
    return dispatch(args.command,args.arguments,console)


if __name__ == "__main__":
    raise SystemExit(main())
