"""Local CLI regressions. No external services, keys or network."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import intel

class LocalCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.environment = patch.dict(os.environ, {"INTEL_CONFIG_HOME": self.temp.name, "NO_COLOR": "1"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def call(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = intel.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_language_persistence_and_fallback(self):
        self.assertEqual(self.call("config", "language", "de")[0], 0)
        self.assertEqual(json.loads(self.call("--json", "config", "language", "show")[1]), {"language": "de"})
        self.assertEqual(self.call("config", "language", "invalid")[0], 2)
        self.assertEqual(intel.read_language(), "de")
        intel.config_path().write_text("{not valid", encoding="utf-8")
        self.assertEqual(intel.read_language(), "en")

    def test_machine_output_is_clean(self):
        code, output, err = self.call("--json", "providers")
        self.assertEqual(code, 0)
        self.assertFalse(err)
        self.assertIn("template", json.loads(output))
        self.assertNotIn("\033", output)

    def test_noninteractive_fails_closed(self):
        self.assertEqual(self.call("--non-interactive")[0], 2)

    def test_generator_has_original_authorization_gate(self):
        code, _, err = self.call("generate", "prompt", "--objective", "Example")
        self.assertEqual(code, 2)
        self.assertIn("PERMISSION_DENIED", err)

    def test_symlink_config_is_rejected(self):
        destination = intel.config_path()
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = Path(self.temp.name) / "outside"
        target.write_text("preserve")
        try:
            destination.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not available")
        self.assertEqual(self.call("config", "language", "de")[0], 3)
        self.assertEqual(target.read_text(), "preserve")

    def test_unsupported_start_is_blocked(self):
        if os.name != "nt":
            self.assertEqual(self.call("start")[0], 3)

if __name__ == "__main__":
    unittest.main()
