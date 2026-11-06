"""Versioned, secret-free CLI preferences. No network, providers or implicit writes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

SCHEMA_VERSION = 1
DEFAULTS = {"schema_version": SCHEMA_VERSION, "language": "en"}
LANGUAGES = frozenset(("en", "de"))
MAX_BYTES = 8192


class ConfigError(ValueError):
    """Invalid configuration, unsafe path or unsupported schema."""


def config_path() -> Path:
    base = os.environ.get("INTEL_CONFIG_HOME")
    if base:
        return Path(base).expanduser() / "config.json"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "ChatGPTIntelligence" / "config.json"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "chatgpt-intelligence" / "config.json"


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"Duplicate configuration key: {key}")
        result[key] = value
    return result


def validate(data: object) -> dict[str, object]:
    """Accept old language-only files; reject unknown fields including secrets."""
    if not isinstance(data, dict):
        raise ConfigError("Configuration must be a JSON object.")
    unknown = set(data) - set(DEFAULTS)
    if unknown:
        raise ConfigError("Unsupported configuration keys: " + ", ".join(sorted(unknown)))
    version = data.get("schema_version", SCHEMA_VERSION)
    if type(version) is not int or version != SCHEMA_VERSION:
        raise ConfigError(f"Unsupported schema_version: {version!r}; expected {SCHEMA_VERSION}.")
    lang = data.get("language", "en")
    if lang not in LANGUAGES or not isinstance(lang, str):
        raise ConfigError("Invalid language; choose en or de.")
    return {"schema_version": SCHEMA_VERSION, "language": lang}


def _read(path: Path, *, absent_ok: bool) -> dict[str, object] | None:
    if path.is_symlink():
        raise ConfigError("Configuration path is a symbolic link. Use a regular file.")
    if not path.exists():
        if absent_ok:
            return None
        raise ConfigError("Configuration file does not exist.")
    if not path.is_file():
        raise ConfigError("Configuration path must be a regular file.")
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ConfigError("Configuration exceeds the 8 KiB limit.")
        with path.open("r", encoding="utf-8-sig") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw.encode("utf-8")) > MAX_BYTES:
            raise ConfigError("Configuration exceeds the 8 KiB limit.")
        return validate(json.loads(raw, object_pairs_hook=_unique_pairs))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read configuration: {type(exc).__name__}.") from exc


def read_user() -> dict[str, object] | None:
    return _read(config_path(), absent_ok=True)


def effective(*, cli_language: str | None = None, environ: dict[str, str] | None = None) -> dict[str, object]:
    """CLI override > INTEL_LANGUAGE > user file > built-in default."""
    env = os.environ if environ is None else environ
    user = read_user()
    language, source = (str(user["language"]), "user") if user else ("en", "default")
    if "INTEL_LANGUAGE" in env:
        language, source = env["INTEL_LANGUAGE"], "environment"
    if cli_language is not None:
        language, source = cli_language, "cli"
    if language not in LANGUAGES:
        raise ConfigError(f"Invalid {source} language. Choose en or de.")
    return {"schema_version": SCHEMA_VERSION, "language": language, "source": source}


def _check_parent(path: Path) -> None:
    """Deny symlink parents without following a symlink into another directory."""
    for directory in (path.parent, *path.parent.parents):
        if directory.is_symlink():
            raise ConfigError("Configuration directory contains a symbolic link.")
    if path.is_symlink():
        raise ConfigError("Refusing to write through a symbolic link.")
    if path.exists() and not path.is_file():
        raise ConfigError("Destination is not a regular file.")


def write_user(data: object) -> bool:
    """Atomic replacement; unchanged configuration is never rewritten."""
    checked = validate(data)
    path = config_path()
    _check_parent(path)
    previous = read_user()
    if previous == checked:
        return False
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _check_parent(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".intel-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(checked, stream, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            temporary.chmod(0o600)
        _check_parent(path)
        os.replace(temporary, path)
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_file(target: Path) -> Path:
    """Explicit exclusive, sanitized export. Never overwrite or follow links."""
    _check_parent(target)
    settings = validate(read_user() or DEFAULTS)
    payload = (json.dumps(settings, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def import_file(source: Path, *, apply: bool = False) -> tuple[dict[str, object], bool]:
    """Preview validated import unless explicitly approved with --apply."""
    checked = _read(source, absent_ok=False)
    assert checked is not None
    if not apply:
        return checked, False
    changed = write_user(checked)
    return checked, changed


def issues() -> list[dict[str, str]]:
    problems = []
    try:
        user = read_user()
        effective()
        if user is None:
            problems.append({"code": "NOT_INITIALIZED", "severity": "info",
                             "fix": "Run intel setup --apply to create the user preferences."})
    except ConfigError as exc:
        problems.append({"code": "INVALID_CONFIG", "severity": "error",
                         "fix": str(exc) + " Review intel config validate before making changes."})
    return problems
