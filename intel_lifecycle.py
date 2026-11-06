"""Owned Windows tunnel runtime. MCP stdio lifecycles belong to their caller.

Only an authenticated local supervisor can shut down its own subprocess.
Never send a signal to a PID read from a status file.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import subprocess
import sys
import time

from intel_config import ConfigError, config_path, _check_parent

HOST = "127.0.0.1"
STATE = "tunnel-runtime.json"
MAX_BYTES = 2048

class LifecycleError(RuntimeError):
    pass

def record_path() -> Path:
    return config_path().parent / STATE

def _read() -> dict | None:
    path = record_path()
    _check_parent(path)
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise LifecycleError("Managed runtime record is invalid; no process was signalled.")
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise LifecycleError("Runtime record permissions are unsafe.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("version") != 1
            or data.get("component") != "tunnel" or type(data.get("pid")) is not int
            or type(data.get("port")) is not int or not 1 <= data["port"] <= 65535
            or not isinstance(data.get("nonce"), str)
            or re.fullmatch("[0-9a-f]{64}", data["nonce"]) is None):
            raise ValueError("invalid fields")
        return data
    except (ValueError, UnicodeError, OSError) as exc:
        raise LifecycleError("Managed runtime record is corrupt; no process was signalled.") from exc

def _send(state: dict, action: str) -> dict:
    with socket.create_connection((HOST, state["port"]), timeout=1) as conn:
        conn.settimeout(2)
        conn.sendall((json.dumps({"nonce": state["nonce"], "action": action}) + "\n").encode())
        message = bytearray()
        while len(message) < MAX_BYTES and not message.endswith(b"\n"):
            block = conn.recv(min(256, MAX_BYTES - len(message)))
            if not block:
                break
            message.extend(block)
    try:
        reply = json.loads(message)
    except (UnicodeError, ValueError) as exc:
        raise LifecycleError("Malformed supervisor response.") from exc
    if (not isinstance(reply, dict) or reply.get("nonce") != state["nonce"]
            or reply.get("pid") != state["pid"] or reply.get("ok") is not True):
        raise LifecycleError("Supervisor identity mismatch; no process was signalled.")
    return reply

def inspect() -> dict:
    try:
        record = _read()
        if record is None:
            return {"state": "not_managed", "ownership": "none"}
        reply = _send(record, "status")
        return {"state": "running" if reply.get("running") else "stopping",
                "ownership": "authenticated", "pid": record["pid"],
                "control_port": record["port"]}
    except (LifecycleError, ConfigError, OSError, TimeoutError):
        return {"state": "unverified", "ownership": "unverified"}

def stop() -> dict:
    record = _read()
    if record is None:
        return {"state": "not_managed", "changed": False}
    try:
        _send(record, "stop")
    except OSError as exc:
        raise LifecycleError("Supervisor unreachable; no process was terminated.") from exc
    for _ in range(80):
        if not record_path().exists():
            return {"state": "stopped", "changed": True}
        time.sleep(0.1)
    raise LifecycleError("Shutdown requested but cleanup could not be verified.")

def _preflight() -> tuple[str, str]:
    if os.name != "nt":
        raise LifecycleError("Managed tunnel startup requires Windows.")
    exe = os.environ.get("INTEL_TUNNEL_CLIENT", "")
    if not exe:
        from shutil import which
        exe = which("tunnel-client.exe") or ""
    if not exe or not Path(exe).is_file() or Path(exe).suffix.lower() != ".exe":
        raise LifecycleError("Set INTEL_TUNNEL_CLIENT to an existing tunnel-client.exe.")
    profile = os.environ.get("INTEL_TUNNEL_PROFILE", "chatgpt-intelligence")
    if re.fullmatch("[a-zA-Z0-9_-]+", profile) is None:
        raise LifecycleError("Invalid tunnel profile name.")
    appdata = os.environ.get("APPDATA", "")
    if not appdata or not (Path(appdata) / "tunnel-client" / (profile + ".yaml")).is_file():
        raise LifecycleError("Tunnel profile missing; configure tunnel-client first.")
    if not os.environ.get("CONTROL_PLANE_API_KEY"):
        raise LifecycleError("Set CONTROL_PLANE_API_KEY explicitly before managed startup.")
    with socket.socket() as probe:
        probe.settimeout(.4)
        if probe.connect_ex((HOST, 8080)) == 0:
            raise LifecycleError("Port 8080 is occupied; no foreign listener was changed.")
    return str(Path(exe).resolve()), profile

def start() -> dict:
    current = inspect()
    if current["state"] == "running":
        return {"state": "running", "changed": False}
    if current["state"] != "not_managed":
        raise LifecycleError("Unverified runtime record; refusing duplicate startup.")
    exe, profile = _preflight()
    path = record_path()
    _check_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _check_parent(path)
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    supervisor = subprocess.Popen([sys.executable, "-m", "intel_lifecycle", "_supervise", exe, profile],
                                  cwd=str(Path(__file__).resolve().parent),
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    for _ in range(60):
        time.sleep(0.1)
        status = inspect()
        if status["state"] == "running":
            return {"state": "running", "changed": True, "pid": status["pid"]}
        if supervisor.poll() is not None:
            raise LifecycleError("Supervisor exited; inspect tunnel profile and local prerequisites.")
    raise LifecycleError("Startup unconfirmed; inspect status before retrying.")

def restart() -> dict:
    current = inspect()
    if current["state"] == "unverified":
        raise LifecycleError("Cannot restart an unverified process.")
    if current["state"] == "running":
        stop()
    return start()

def _stop_child(child: subprocess.Popen) -> None:
    if child.poll() is not None:
        return
    try:
        child.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM)
        child.wait(timeout=4)
    except (OSError, subprocess.TimeoutExpired):
        if child.poll() is None:
            child.kill()  # Direct child Popen handle, NEVER a disk-record PID.
            child.wait(timeout=4)

def supervise(exe: str, profile: str) -> int:
    child = None
    nonce = secrets.token_hex(32)
    path = record_path()
    created = False
    with socket.socket() as server:
        try:
            _check_parent(path)
            server.bind((HOST, 0))
            server.listen(4)
            server.settimeout(.3)
            flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            child = subprocess.Popen([exe, "run", "--profile", profile], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=flags, close_fds=True)
            if child.poll() is not None:
                return 3
            payload = {"version": 1, "component": "tunnel", "pid": os.getpid(),
                       "port": server.getsockname()[1], "nonce": nonce}
            options = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(path, options, 0o600)
            created = True
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            while child.poll() is None:
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    conn.settimeout(.8)
                    raw = bytearray()
                    try:
                        while len(raw) < MAX_BYTES and not raw.endswith(b"\n"):
                            part = conn.recv(min(256, MAX_BYTES - len(raw)))
                            if not part:
                                break
                            raw.extend(part)
                        request = json.loads(raw)
                        action = request.get("action") if (isinstance(request, dict) and
                            secrets.compare_digest(str(request.get("nonce", "")), nonce)) else None
                    except (socket.timeout, OSError, ValueError, UnicodeError):
                        action = None
                    response = {"nonce": nonce if action else "", "pid": os.getpid(),
                                "ok": action in ("status", "stop"), "running": child.poll() is None}
                    try:
                        conn.sendall((json.dumps(response) + "\n").encode())
                    except OSError:
                        pass
                    if action == "stop":
                        break
            return 0
        finally:
            if child:
                _stop_child(child)
            if created:
                try:
                    current = _read()
                    if current and current["nonce"] == nonce and current["pid"] == os.getpid():
                        path.unlink()
                except (LifecycleError, ConfigError, OSError):
                    pass

def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] != "_supervise":
        return 2
    try:
        return supervise(sys.argv[2], sys.argv[3])
    except (OSError, LifecycleError, ConfigError):
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
