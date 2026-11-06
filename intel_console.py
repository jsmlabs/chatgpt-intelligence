"""Shared stdlib-only console renderer with width, ANSI, and keyboard fallbacks."""
from __future__ import annotations

import json
import os
import shutil
import sys
import textwrap
import unicodedata
from typing import TextIO
from intel_locales import tr

COLORS = {"info":"36","pass":"32","warn":"33","fail":"31","skip":"90","blocked":"31","accent":"35","muted":"90"}
LABELS = {"pass":"PASS","warn":"WARN","fail":"FAIL","skip":"SKIP","blocked":"BLOCKED"}


def _windows_vt(stream: TextIO) -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.SetConsoleMode.restype = wintypes.BOOL
        handle = kernel.GetStdHandle(-11 if stream is sys.stdout else -12)
        mode = wintypes.DWORD()
        return bool(handle and kernel.GetConsoleMode(handle, ctypes.byref(mode))
                    and ((mode.value & 4) or kernel.SetConsoleMode(handle, mode.value | 4)))
    except (AttributeError, OSError, ValueError):
        return False


def ansi_supported(stream: TextIO, *, disabled: bool = False) -> bool:
    return bool(not disabled and "NO_COLOR" not in os.environ
                and os.environ.get("TERM") != "dumb" and getattr(stream, "isatty", lambda: False)()
                and _windows_vt(stream))


def cell_width(value: str) -> int:
    return sum(0 if unicodedata.combining(c) or unicodedata.category(c) in ("Cc", "Cf")
               else 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in value)


def truncate(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if cell_width(value) <= limit:
        return value
    result = ""
    for c in value:
        if cell_width(result + c) > limit - 1:
            break
        result += c
    return result + "…"


class Console:
    def __init__(self, *, language: str, json_mode: bool = False, quiet: bool = False,
                 no_color: bool = False, stream: TextIO | None = None,
                 error_stream: TextIO | None = None):
        self.language, self.json_mode, self.quiet = language, json_mode, quiet
        self.stream, self.error_stream = stream or sys.stdout, error_stream or sys.stderr
        self.color = not json_mode and ansi_supported(self.stream, disabled=no_color)
        self.error_color = not json_mode and ansi_supported(self.error_stream, disabled=no_color)

    def tr(self, key: str, **values: object) -> str:
        return tr(self.language, key, **values)

    @property
    def width(self) -> int:
        return max(32, min(120, shutil.get_terminal_size((80, 24)).columns))

    def _print(self, value: str, kind: str = "info", *, error: bool = False) -> None:
        if self.quiet and not error:
            return
        stream = self.error_stream if error else self.stream
        colored = self.error_color if error else self.color
        value = f"\x1b[{COLORS.get(kind, '36')}m{value}\x1b[0m" if colored else value
        print(value, file=stream)

    def emit(self, message: str, kind: str = "info") -> None:
        prefix = "[" + LABELS[kind] + "] " if kind in LABELS else ""
        for line in (prefix + message).splitlines() or [""]:
            self._print(line, kind)

    def error(self, message: str, kind: str = "fail") -> None:
        self._print(f"[{LABELS.get(kind, 'FAIL')}] {message}", kind, error=True)

    def header(self, title: str, subtitle: str = "") -> None:
        if self.json_mode or self.quiet:
            return
        line = ("─" if self.color else "-") * min(self.width, 72)
        self._print(line, "muted")
        self._print(truncate(title, self.width), "info")
        if subtitle:
            self._print(truncate(subtitle, self.width), "muted")
        self._print(line, "muted")

    def table(self, rows: list[tuple[str, str, str]], title: str = "") -> None:
        if title:
            self.header(title)
        if self.quiet or self.json_mode:
            return
        label_width = min(26, max(12, self.width // 3))
        value_width = max(8, self.width - label_width - 3)
        for label, value, status in rows:
            text = textwrap.wrap(str(value), value_width, break_long_words=True,
                                 break_on_hyphens=False) or [""]
            for index, part in enumerate(text):
                first = truncate(label, label_width).ljust(label_width) if index == 0 else " " * label_width
                self._print(f"{first}  {truncate(part, value_width)}", status)

    def report(self, data: dict[str, object], title: str = "") -> None:
        if self.json_mode:
            print(json.dumps(data, sort_keys=True, ensure_ascii=False), file=self.stream)
            return
        rows = []
        for key, value in data.items():
            if isinstance(value, bool):
                rendered, status = self.tr("available" if value else "missing"), "pass" if value else "warn"
            elif isinstance(value, str) and value in ("offline", "not_contacted", "not_checked", "host_required", "explicit_grant"):
                rendered = self.tr(value)
                status = "pass" if value == "offline" else "warn"
            else:
                rendered, status = str(value), "info"
            rows.append((self.tr(key), rendered, status))
        self.table(rows, title)

    def menu(self, commands: tuple[str, ...], descriptions: dict[str, str], selected: int | None = None) -> None:
        self.header(self.tr("title"), self.tr("subtitle"))
        for i, name in enumerate(commands):
            marker = ">" if i == selected else " "
            line = f"{marker} {i+1:02}  {self.tr(name)}  -  {descriptions[name]}"
            self._print(truncate(line, self.width), "accent" if selected == i else "info")
        self._print(f"  00  {self.tr('exit')}", "muted")
        self._print(truncate(self.tr("menu_hint"), self.width), "muted")

    def ask(self, prompt: str) -> str:
        return input(prompt)


def read_key() -> str:
    """Arrow keys, Enter and Escape on true TTY; no third-party terminal dependency."""
    if os.name == "nt":
        import msvcrt
        c = msvcrt.getwch()
        if c in ("\x00", "\xe0"):
            return {"H":"up","P":"down"}.get(msvcrt.getwch(), "")
        return {"\r":"enter","\x1b":"exit","\x03":"exit"}.get(c, c)
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        c = sys.stdin.read(1)
        if c == "\x1b":
            if select.select([sys.stdin], [], [], .08)[0] and sys.stdin.read(1) == "[":
                if select.select([sys.stdin], [], [], .08)[0]:
                    return {"A":"up","B":"down"}.get(sys.stdin.read(1), "")
            return "exit"
        return {"\r":"enter","\n":"enter","\x03":"exit"}.get(c, c)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)
