"""Local Ollama smoke verifier policy tests. No live model or network."""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from generators.model_host import ModelOutput
from scripts import verify_ollama_live


class FakeLocal:
    configured = True

    def __init__(self, **kwargs):
        self.calls = 0

    def available(self):
        return True

    def generate(self, kind, brief):
        self.calls += 1
        return ModelOutput("# " + kind + "\n\n## Draft\n\nText.", "ollama-local", "fixture", "")


class LocalVerifierTests(unittest.TestCase):
    def test_unapproved_and_unconfigured_do_not_probe(self):
        for args, expected in (
            ([], "explicit local authorization required"),
            (["--authorize-local-inference"], "local model not configured"),
        ):
            with self.subTest(args=args):
                env = dict(os.environ)
                env.pop("INTEL_OLLAMA_MODEL", None)
                result = subprocess.run(
                    [sys.executable, "-m", "scripts.verify_ollama_live", *args],
                    capture_output=True, text=True, env=env, check=False)
                self.assertEqual(result.returncode, 2)
                data = json.loads(result.stdout)
                self.assertEqual(data["reason"], expected)
                self.assertEqual(data["status"], "BLOCKED")

    def test_two_local_generators_pass_without_billable_grant(self):
        capture = io.StringIO()
        with patch.object(verify_ollama_live, "OllamaLocalHost", FakeLocal):
            with contextlib.redirect_stdout(capture):
                code = verify_ollama_live.main(["--authorize-local-inference"])
        self.assertEqual(code, 0)
        data = json.loads(capture.getvalue())
        self.assertEqual(data["status"], "PASSED")
        self.assertEqual([x["type"] for x in data["results"]], ["PROMPT", "DOCUMENT"])
        self.assertTrue(all(x["balanced_code_fences"] for x in data["results"]))
        self.assertNotIn("## Draft", capture.getvalue())

    def test_unreachable_model_blocks_without_generation(self):
        class Offline(FakeLocal):
            def available(self):
                return False
            def generate(self, kind, brief):
                self.fail("should not be called")
        capture = io.StringIO()
        with patch.object(verify_ollama_live, "OllamaLocalHost", Offline):
            with contextlib.redirect_stdout(capture):
                code = verify_ollama_live.main(["--authorize-local-inference"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(capture.getvalue())["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
