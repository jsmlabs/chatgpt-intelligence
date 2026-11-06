"""Owned-process lifecycle tests; never contact a real tunnel or model."""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import intel
import intel_lifecycle as life


class FakeChild:
    def __init__(self):
        self.alive = True
        self.signals = []
    def poll(self):
        return None if self.alive else 0
    def send_signal(self, sig):
        self.signals.append(sig)
        self.alive = False
    def wait(self, timeout=None):
        self.alive = False
        return 0
    def kill(self):
        self.alive = False


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.env = patch.dict(os.environ, {"INTEL_CONFIG_HOME": temp.name, "NO_COLOR": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.home = Path(temp.name)

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = intel.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_unmanaged_status_and_safe_stop(self):
        self.assertEqual(life.inspect()["state"], "not_managed")
        self.assertEqual(self.cli("stop")[0], 0)
        self.assertEqual(life.inspect()["state"], "not_managed")
        self.assertEqual(self.cli("restart", "mcp")[0], 2)
        self.assertEqual(self.cli("start", "mcp")[0], 2)
        self.assertIn("host_owned", json.loads(self.cli("--json", "status")[1]).values())

    def test_stale_record_never_kills_foreign_process(self):
        path = life.record_path()
        path.write_text(json.dumps({"version":1,"component":"tunnel","pid":os.getpid(),
                                    "port":1,"nonce":"f"*64}), encoding="utf-8")
        if os.name != "nt":
            path.chmod(0o600)
        self.assertEqual(life.inspect()["state"], "unverified")
        with patch("os.kill") as kill:
            self.assertEqual(self.cli("stop")[0], 3)
            self.assertEqual(self.cli("restart")[0], 3)
            kill.assert_not_called()
        self.assertTrue(path.exists())

    def test_corrupt_record_not_removed(self):
        path = life.record_path()
        path.write_text('{"pid":false}', encoding="utf-8")
        self.assertEqual(self.cli("stop")[0], 3)
        self.assertTrue(path.exists())

    def test_authenticated_loopback_and_child_ownership(self):
        child = FakeChild()
        results = []
        with patch.object(life.subprocess, "Popen", return_value=child):
            thread = threading.Thread(target=lambda: results.append(life.supervise("fake.exe", "profile")))
            thread.start()
            try:
                for _ in range(100):
                    if life.inspect()["state"] == "running":
                        break
                    time.sleep(.02)
                self.assertEqual(life.inspect()["ownership"], "authenticated")
                record = life._read()
                self.assertEqual(record["pid"], os.getpid())
                wrong = dict(record, nonce="0"*64)
                with self.assertRaises(life.LifecycleError):
                    life._send(wrong, "stop")
                self.assertTrue(child.alive)
                self.assertEqual(life.stop()["state"], "stopped")
                self.assertEqual(len(child.signals), 1)
            finally:
                thread.join(timeout=4)
            self.assertFalse(thread.is_alive())
            self.assertEqual(results, [0])
        self.assertFalse(life.record_path().exists())

    def test_symlink_runtime_record_blocks_without_signals(self):
        path = life.record_path()
        target = self.home / "outside.json"
        target.write_text("{}")
        try:
            path.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("No symlink support")
        self.assertEqual(life.inspect()["state"], "unverified")
        with patch("os.kill") as kill:
            self.assertEqual(self.cli("stop")[0], 3)
            kill.assert_not_called()
        self.assertEqual(target.read_text(), "{}")

    def test_non_windows_managed_start_fails_closed(self):
        if os.name != "nt":
            self.assertEqual(self.cli("start", "--managed")[0], 3)
        self.assertEqual(self.cli("stop", "--managed")[0], 2)

    def test_runtime_record_does_not_leak_into_config_export(self):
        self.home.joinpath("tunnel-runtime.json").write_text("sensitive-runtime-nonce")
        export = self.home / "export.json"
        self.assertEqual(self.cli("config", "export", str(export))[0], 0)
        self.assertNotIn("sensitive-runtime-nonce", export.read_text())

if __name__ == "__main__":
    unittest.main()
