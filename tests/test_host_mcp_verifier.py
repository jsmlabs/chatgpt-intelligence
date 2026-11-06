"""G1.9 local stdio handoff verifier tests."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest


class HostMcpVerifierTests(unittest.TestCase):
    def test_explicit_create_required(self):
        result = subprocess.run([sys.executable, "-m", "scripts.verify_host_mcp"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "BLOCKED")

    def test_real_stdio_three_submissions(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.verify_host_mcp", "--authorize-local-create"],
            capture_output=True, text=True, timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "PASSED")
        self.assertEqual(len(data["results"]), 3)
        self.assertFalse(data["chatgpt_client_connected"])
        self.assertFalse(data["paid_provider_invoked"])


if __name__ == "__main__":
    unittest.main()
