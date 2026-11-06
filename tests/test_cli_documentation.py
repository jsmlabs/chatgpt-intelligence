"""Validate documentation command examples against the real CLI contract.

No external providers, filesystem mutations or network calls are involved.
"""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import intel
from generators.capabilities import GENERATOR_NAMES
from intel_locales import CATALOGS


ROOT = Path(__file__).resolve().parent.parent
DOCS = (
    "COMMANDS.md",
    "LOCAL_CLI.md",
    "architecture/local-runtime.md",
    "guides/local-cli-migration.md",
    "guides/local-cli-extension.md",
    "guides/local-cli-troubleshooting.md",
)


class CLIDocumentationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"INTEL_CONFIG_HOME": temp.name, "NO_COLOR": "1"})
        env.start()
        self.addCleanup(env.stop)

    def call(self, *args):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = intel.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_references_exist_and_links_are_rooted(self):
        for item in DOCS:
            with self.subTest(document=item):
                self.assertTrue((ROOT / item).is_file())
        self.assertEqual(set(CATALOGS["en"]), set(CATALOGS["de"]))

    def test_runtime_documentation_names_actual_modules(self):
        architecture = (ROOT / "architecture/local-runtime.md").read_text(encoding="utf-8")
        for file in ("intel.py", "intel_console.py", "intel_locales.py", "intel_config.py",
                     "intel_lifecycle.py", "intel_devtools.py", "generators/capabilities.py",
                     "generators/provider_router.py", "generators/__main__.py",
                     "generators/mcp_server.py"):
            with self.subTest(file=file):
                self.assertIn(file, architecture)
                self.assertTrue((ROOT / file).is_file(), file)

    def test_documented_commands_are_discoverable(self):
        command_text = (ROOT / "COMMANDS.md").read_text(encoding="utf-8")
        self.assertIn("Current executable local command reference", command_text)
        for command in ("help", "version", "generators", "capabilities", "providers",
                        "doctor", "config", "setup", "status", "test", "check", "verify",
                        "dev", "clean", "update", "logs", "start", "stop", "restart",
                        "generate"):
            self.assertIn(command, intel.COMMANDS)
        self.assertEqual(len(GENERATOR_NAMES), 10)
        self.assertNotIn("video", GENERATOR_NAMES)

    def test_read_only_example_execution(self):
        examples = (
            ("help",),
            ("--json", "version"),
            ("--json", "capabilities"),
            ("--json", "providers"),
            ("--json", "doctor", "basic"),
            ("--json", "clean"),
            ("--json", "logs"),
            ("setup",),
        )
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
            for args in examples:
                with self.subTest(args=args):
                    code, out, err = self.call(*args)
                    self.assertEqual((code, err), (0, ""), args)
                    self.assertTrue(out)
                    if args[0] == "--json":
                        self.assertIsInstance(json.loads(out), dict)
                        self.assertNotIn("\x1b", out)
        self.assertFalse(intel.config_path().exists(), "read-only examples wrote configuration")

    def test_dangerous_or_unverified_examples_fail_closed(self):
        self.assertEqual(self.call("clean", "--apply")[0], 3)
        self.assertEqual(self.call("generate", "prompt", "--objective", "Demo")[0], 2)
        self.assertEqual(self.call("--json", "verify", "mcp")[0], 3)
        if os.name != "nt":
            self.assertEqual(self.call("start", "--managed")[0], 3)
        self.assertFalse(intel.config_path().exists())


if __name__ == "__main__":
    unittest.main()
