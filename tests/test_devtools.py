"""Offline developer toolkit regressions: profiles, dry runs, redaction, exit codes."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import intel
import intel_devtools as dt


class DeveloperToolsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        environment = patch.dict(os.environ, {
            "INTEL_CONFIG_HOME": temp.name, "NO_COLOR": "1"
        })
        environment.start()
        self.addCleanup(environment.stop)

    def cli(self, *args):
        output, errors = StringIO(), StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = intel.main(list(args))
        return code, output.getvalue(), errors.getvalue()

    def test_json_command_contract(self):
        for args in (("doctor", "basic"), ("doctor", "full"),
                     ("clean",), ("update",), ("logs",)):
            with self.subTest(args=args):
                code, output, errors = self.cli("--json", *args)
                self.assertEqual(code, 0, errors)
                self.assertFalse(errors)
                data = json.loads(output)
                self.assertEqual(data["schema_version"], 1)
                self.assertEqual(data["command"], args[0])
                self.assertEqual(data["exit_code"], 0)
                self.assertIn("checks", data)
                self.assertNotIn("\x1b", output)

    def test_dev_shortcuts_read_only(self):
        code, output, _ = self.cli("--json", "dev")
        self.assertEqual(code, 0)
        self.assertIn("maintenance", json.loads(output)["commands"])
        self.assertFalse((self.root / "config.json").exists())

    def test_cleanup_is_always_preview(self):
        path = self.root / "valuable.txt"
        path.write_text("preserve", encoding="utf-8")
        with patch("pathlib.Path.unlink", side_effect=AssertionError("delete forbidden")):
            code, output, _ = self.cli("--json", "clean")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["status"], "preview")
        self.assertEqual(self.cli("clean", "--apply")[0], 3)
        self.assertEqual(path.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(self.cli("clean", "all")[0], 2)

    def test_update_has_no_network_and_no_claimed_freshness(self):
        report = dt.update()
        self.assertIsNone(report["update_available"])
        self.assertFalse(report["remote_checked"])
        with patch("intel_devtools.subprocess.run") as runner:
            runner.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            report = dt.update()
        for args, _ in runner.call_args_list:
            self.assertNotIn("fetch", args[0])
            self.assertNotIn("pull", args[0])
            self.assertNotIn("ls-remote", args[0])
        self.assertFalse(report["remote_checked"])

    def test_logs_redact_and_limit(self):
        log = self.root / "run.log"
        secret = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz1234567890"
        token = "ghp_" + "x"*36
        log.write_text(
            f'Authorization: Bearer abcDEF123.456\n'
            f'api_key={secret}\n'
            f'{{"token":"{token}"}}\n'
            f'normal status=ready\n', encoding="utf-8")
        code, raw, errors = self.cli("--json", "logs", "--file", str(log))
        self.assertEqual((code, errors), (0, ""))
        self.assertNotIn(secret, raw)
        self.assertNotIn(token, raw)
        self.assertNotIn("abcDEF123.456", raw)
        self.assertIn("[REDACTED]", raw)
        lines = json.loads(raw)["lines"]
        self.assertEqual(len(lines), 4)
        self.assertIn("normal status=ready", lines)

    def test_logs_reject_symlinks_and_oversized(self):
        source = self.root / "large.log"
        source.write_bytes(b"x" * (dt.MAX_LOG_BYTES + 1))
        self.assertEqual(self.cli("logs", "--file", str(source))[0], 2)
        target = self.root / "plain.log"
        target.write_text("okay", encoding="utf-8")
        alias = self.root / "alias.log"
        try:
            alias.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not available")
        self.assertEqual(self.cli("logs", "--file", str(alias))[0], 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "okay")

    def test_check_profiles_delegate_without_extra_scripts(self):
        with patch("intel_devtools.subprocess.run") as runner:
            runner.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            report = dt.check("all")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(runner.call_count, 2)
        args = [call.args[0] for call in runner.call_args_list]
        self.assertIn("scripts/check_docs.py", args[0])
        self.assertIn("unittest", args[1])
        for call in runner.call_args_list:
            self.assertEqual(call.kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(call.kwargs["stderr"], subprocess.DEVNULL)

    def test_check_failure_stops_sequence_and_preserves_exit(self):
        with patch("intel_devtools.subprocess.run") as runner:
            runner.return_value = subprocess.CompletedProcess([], 1)
            report = dt.check("all")
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(runner.call_count, 1)
        code, data, _ = self.cli("--json", "verify", "mcp")
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(data)["status"], "blocked")

    def test_mcp_requires_explicit_grant_and_release_blocks(self):
        with patch("intel_devtools.subprocess.run") as runner:
            runner.return_value = subprocess.CompletedProcess([], 0)
            self.assertEqual(dt.verify("mcp")["exit_code"], 3)
            self.assertEqual(runner.call_count, 0)
            self.assertEqual(dt.verify("mcp", authorize_local_create=True)["exit_code"], 0)
            self.assertIn("--authorize-local-create", runner.call_args.args[0])
            runner.return_value = subprocess.CompletedProcess([], 1)
            report = dt.verify("release")
            self.assertEqual(report["exit_code"], 1)
            self.assertNotIn("--report-only", runner.call_args.args[0])

    def test_timed_out_checks_fail_closed(self):
        with patch("intel_devtools.subprocess.run", side_effect=subprocess.TimeoutExpired("tests", 2)):
            self.assertEqual(dt.check("tests")["exit_code"], 3)

    def test_localization_and_legacy(self):
        self.assertEqual(self.cli("config", "language", "de")[0], 0)
        self.assertIn("Bereinigung", self.cli("help")[1])
        self.assertIn("Entwickler", self.cli("dev")[1])
        code, _, error = self.cli("verify", "mcp", "--bad")
        self.assertEqual(code, 2)
        self.assertIn("[BLOCKED]", error)
        self.assertEqual(self.cli("capabilities")[0], 0)
        # Legacy unprofiled doctor still yields the original inspection shape.
        self.assertIn("generator_package", json.loads(self.cli("--json", "doctor")[1]))


if __name__ == "__main__":
    unittest.main()
