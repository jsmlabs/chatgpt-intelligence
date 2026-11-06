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
import intel_config as configuration
import intel_lifecycle as lifecycle
import intel_devtools as devtools

ROOT = Path(__file__).resolve().parent
VERSION = "0.1.0"
COMMANDS = ("help", "version", "generate", "generators", "capabilities", "config", "providers", "doctor", "status",
            "setup", "start", "stop", "restart", "test", "check", "verify", "dev", "clean", "update", "logs")
INSPECTION = frozenset(("help", "version", "config", "providers", "generators", "capabilities", "doctor", "status", "setup", "check", "verify", "dev", "clean", "update", "logs"))


def config_path() -> Path:
    return configuration.config_path()


def read_language() -> str:
    try:
        return str(configuration.effective()["language"])
    except (configuration.ConfigError, OSError):
        return "en"  # Keep help and repair commands reachable.


def save_language(language: str) -> None:
    configuration.write_user({"language": language})


def parser(language: str | None = None) -> argparse.ArgumentParser:
    lang = language or read_language()
    p = argparse.ArgumentParser(prog="intel", description=tr(lang, "parser_desc"),
                                epilog=tr(lang, "parser_epilog"))
    p.add_argument("--json", action="store_true", help=tr(lang, "opt_json"))
    p.add_argument("--quiet", action="store_true", help=tr(lang, "opt_quiet"))
    p.add_argument("--verbose", action="store_true", help=tr(lang, "opt_verbose"))
    p.add_argument("--no-color", action="store_true", help=tr(lang, "opt_no_color"))
    p.add_argument("--non-interactive", action="store_true", help=tr(lang, "opt_noninteractive"))
    p.add_argument("--language", choices=("en", "de"), help=tr(lang, "opt_language"))
    p.add_argument("command", nargs="?", choices=COMMANDS)
    p.add_argument("arguments", nargs=argparse.REMAINDER)
    return p


def inspect(command: str, language: str | None = None) -> dict[str, object]:
    if command == "version":
        return {"cli_version": VERSION}
    if command in ("providers", "generators", "capabilities"):
        from generators.capabilities import capability_report, generators_report, providers_report
        if command == "generators":
            return generators_report()
        if command == "providers":
            return providers_report()
        return capability_report()
    if command == "status":
        runtime = lifecycle.inspect()
        return {"local_generator":(ROOT / "generators" / "__main__.py").is_file(),
                "mcp_server":(ROOT / "generators" / "mcp_server.py").is_file(),
                "mcp_lifecycle":"host_owned","managed_tunnel":runtime["state"],
                "managed_ownership":runtime["ownership"],
                "tunnel":"not_checked","language":language or read_language()}
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
        if args == ["language", "show"]:
            console.report({"language": console.language})
            return 0
        if not args or args == ["show"]:
            try:
                result = configuration.effective(cli_language=getattr(console, "language_override", None))
            except (configuration.ConfigError, OSError) as exc:
                console.error(console.tr("config_invalid", reason=exc), "blocked")
                return 3
            console.report(result, console.tr("config"))
            return 0
        if args == ["validate"]:
            problems = configuration.issues()
            if problems:
                if any(p["severity"] == "error" for p in problems):
                    for issue in problems:
                        console.error(console.tr("config_invalid", reason=issue["fix"]), "blocked")
                    return 3
                for issue in problems:
                    console.emit(console.tr("config_hint", hint=issue["fix"]), "warn")
            console.report({"valid": True, "schema_version": configuration.SCHEMA_VERSION})
            return 0
        if len(args) == 2 and args[0] == "language" and args[1] in CATALOGS:
            try:
                save_language(args[1])
            except (OSError, configuration.ConfigError) as exc:
                console.error(console.tr("save_failed", error=exc))
                return 3
            console.language = args[1]
            console.report({"language": args[1]})
            return 0
        if len(args) == 2 and args[0] == "export":
            try:
                target = configuration.export_file(Path(args[1]))
            except (OSError, configuration.ConfigError) as exc:
                console.error(console.tr("config_export_failed", reason=type(exc).__name__), "blocked")
                return 3
            console.report({"exported": str(target)})
            return 0
        if len(args) in (2, 3) and args[0] == "import" and (len(args) == 2 or args[2] == "--apply"):
            try:
                data, changed = configuration.import_file(Path(args[1]), apply=len(args) == 3)
            except (OSError, configuration.ConfigError) as exc:
                console.error(console.tr("config_invalid", reason=exc), "blocked")
                return 3
            console.report({"language": data["language"], "schema_version": data["schema_version"],
                            "applied": len(args) == 3, "changed": changed})
            if len(args) == 2:
                console.emit(console.tr("config_import_preview"), "warn")
            return 0
        console.error(console.tr("config_usage"))
        return 2
    if command == "setup":
        if args not in ([], ["--apply"]):
            console.error(console.tr("setup_usage"))
            return 2
        problems = configuration.issues()
        if any(issue["severity"] == "error" for issue in problems):
            for issue in problems:
                console.error(console.tr("config_invalid", reason=issue["fix"]), "blocked")
            return 3
        if not args:
            console.report({"configured": configuration.read_user() is not None,
                            "config_path": str(configuration.config_path()),
                            "schema_version": configuration.SCHEMA_VERSION,
                            "language": console.language})
            console.emit(console.tr("setup_preview"), "warn")
            return 0
        try:
            previous = configuration.read_user()
            changed = configuration.write_user(previous or configuration.DEFAULTS)
        except (OSError, configuration.ConfigError) as exc:
            console.error(console.tr("save_failed", error=exc), "blocked")
            return 3
        console.report({"configured": True, "changed": changed,
                        "schema_version": configuration.SCHEMA_VERSION})
        return 0
    if command in ("doctor", "check", "verify", "clean", "update", "logs", "dev"):
        # Legacy doctor, check, verify and test entrypoints keep their prior
        # behavior without a profile; JSON requests use bounded reports.
        if command == "doctor" and not args:
            console.report(inspect("doctor", console.language), console.tr("doctor"))
            return 0
        if command == "doctor" and args not in (["basic"], ["full"]):
            console.error(console.tr("unexpected", command=command, args=" ".join(args)))
            return 2
        if command == "check" and not args and not console.json_mode:
            code = run_script("scripts/check_docs.py", console, "--root", ".")
            return code if code else dispatch("test", [], console)
        if command == "verify" and not args and not console.json_mode:
            return run_script("scripts/verify_host_mcp.py", console)
        if command == "dev" and not args:
            console.report(devtools.shortcuts(), console.tr("dev"))
            return 0
        try:
            if command == "doctor":
                if len(args) != 1 or args[0] not in devtools.DOCTOR_PROFILES:
                    raise ValueError("doctor [basic|full]")
                report = devtools.doctor(args[0])
            elif command == "check":
                profile = args[0] if args else "all"
                if len(args) > 1 or profile not in devtools.CHECK_PROFILES:
                    raise ValueError("check [docs|tests|all|safety]")
                report = devtools.check(profile)
            elif command == "verify":
                profile = args[0] if args else "mcp"
                flags = args[1:] if args else []
                if profile not in devtools.VERIFY_PROFILES or flags not in ([], ["--authorize-local-create"]) or (flags and profile != "mcp"):
                    raise ValueError("verify [mcp [--authorize-local-create]|release]")
                report = devtools.verify(profile, authorize_local_create=bool(flags))
            elif command == "clean":
                if args == ["--apply"]:
                    console.error(console.tr("devtool_clean_blocked"), "blocked")
                    return 3
                if args:
                    raise ValueError("clean (preview only)")
                report = devtools.clean()
            elif command == "update":
                if args:
                    raise ValueError("update (offline inspection only)")
                report = devtools.update()
            elif command == "logs":
                if args and (len(args) != 2 or args[0] != "--file"):
                    raise ValueError("logs [--file PATH]")
                report = devtools.logs(Path(args[1]) if args else None)
            else:
                raise ValueError("dev (no arguments)")
        except (ValueError, OSError, devtools.ConfigError) as exc:
            console.error(console.tr("devtool_error", reason=str(exc)), "blocked")
            return 2 if isinstance(exc, ValueError) and not isinstance(exc, devtools.ConfigError) else 3
        console.report(report, console.tr(command))
        return int(report["exit_code"])
    if command in ("stop", "restart") or (command == "start" and args == ["--managed"]):
        if command == "start" and args != ["--managed"]:
            return 2
        if command != "start" and args:
            console.error(console.tr("runtime_usage"))
            return 2
        try:
            result = {"start": lifecycle.start, "stop": lifecycle.stop,
                      "restart": lifecycle.restart}[command]()
        except (lifecycle.LifecycleError, configuration.ConfigError, OSError) as exc:
            console.error(console.tr("runtime_error", reason=exc), "blocked")
            return 3
        console.report(result, console.tr(command))
        return 0
    if command == "start" and args:
        console.error(console.tr("runtime_usage"))
        return 2
    if args:
        console.error(console.tr("unexpected", command=command, args=" ".join(args)))
        return 2
    if command in ("version","providers","generators","capabilities","status"):
        console.report(inspect(command, console.language), console.tr(command))
        return 0
    if command == "test":
        return subprocess.run([sys.executable,"-m","unittest","discover","-s","tests"],
                              cwd=str(ROOT),check=False).returncode
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
    try:
        language = str(configuration.effective(cli_language=args.language)["language"])
    except (configuration.ConfigError, OSError):
        language = args.language or "en"  # Allow repair commands even with broken config.
    console = Console(language=language,json_mode=args.json,
                      quiet=args.quiet,no_color=args.no_color)
    console.language_override = args.language
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
    if args.quiet and args.command in ("generate","test","check","verify","start","stop","restart"):
        console.error(console.tr("quiet_unsupported"))
        return 2
    if args.verbose and not args.quiet and not args.json:
        print(f"intel {args.command}", file=sys.stderr)
    return dispatch(args.command,args.arguments,console)


if __name__ == "__main__":
    raise SystemExit(main())
