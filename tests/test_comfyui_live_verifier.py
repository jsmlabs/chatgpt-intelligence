"""G2.1.3 preflight/live verifier - synthetic only; no real ComfyUI."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from generators.comfyui_image import ComfyUIHost, ComfyImage
from generators.foundation import IntelError
from generators.image_render import render_abstract_png
from scripts.verify_comfyui_live import report
import hashlib

MODEL = "synthetic.safetensors"


class FakeHost:
    checkpoint = MODEL
    configured = True
    def __init__(self, *, models=None, failure=None):
        self.models = [MODEL] if models is None else models
        self.failure = failure
        self.calls = 0

    def _json(self, path):
        assert path == "/models/checkpoints"
        return self.models

    def generate(self, prompt, *, authorization, width, height, steps, seed):
        self.calls += 1
        if self.failure:
            raise IntelError(self.failure, "Synthetic failure")
        png = render_abstract_png("fixture")
        return ComfyImage(png, 384, 384, hashlib.sha256(png).hexdigest(), MODEL,
                          "44ebee35-0c62-4b26-9b05-c9b54161a355")


class VerifierTests(unittest.TestCase):
    def test_preflight_never_queues(self):
        fake = FakeHost()
        data = report(fake)
        self.assertEqual(data["status"], "READY")
        self.assertEqual(data["checkpoint_count"], 1)
        self.assertEqual(data["reason"], "inference_not_authorized")
        self.assertEqual(fake.calls, 0)

    def test_missing_model_blocks_without_queue(self):
        fake = FakeHost(models=[])
        result = report(fake, authorize=True, output_dir=Path("."))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reason"], "checkpoint_not_installed")
        self.assertEqual(fake.calls, 0)

    def test_bad_inventory_blocks(self):
        for models in ({"models": [MODEL]}, [None], ["x"] * 1025):
            with self.subTest(models=repr(models)[:50]):
                data = report(FakeHost(models=models))
                self.assertEqual(data["status"], "BLOCKED")
                self.assertEqual(data["reason"], "MODEL_RESPONSE_INVALID")

    def test_output_required_before_queue(self):
        fake = FakeHost()
        data = report(fake, authorize=True)
        self.assertEqual(data["reason"], "output_directory_required")
        self.assertEqual(fake.calls, 0)

    def test_live_synthetic_export(self):
        fake = FakeHost()
        with tempfile.TemporaryDirectory() as folder:
            data = report(fake, authorize=True, output_dir=Path(folder),
                          filename="test-comfy.png")
            self.assertEqual(data["status"], "PASSED")
            self.assertEqual(fake.calls, 1)
            self.assertTrue(data["image_verified"])
            self.assertTrue(data["file_verified"])
            self.assertEqual(hashlib.sha256((Path(folder) / "test-comfy.png").read_bytes()).hexdigest(),
                             data["sha256"])
            self.assertFalse(data["paid_provider_invoked"])

    def test_queue_failure_not_claimed_passed(self):
        data = report(FakeHost(failure="MODEL_TIMEOUT"), authorize=True,
                      output_dir=Path("."))
        self.assertEqual(data["status"], "BLOCKED")
        self.assertEqual(data["reason"], "MODEL_TIMEOUT")
        self.assertFalse(data["image_generated"])
        self.assertTrue(data["inference_may_still_be_running"])

    def test_deny_default_without_any_comfy_server(self):
        run = subprocess.run([sys.executable, "-m", "scripts.verify_comfyui_live",
                              "--checkpoint", ""], text=True, capture_output=True,
                             timeout=10)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("PASSED", run.stdout)


if __name__ == "__main__":
    unittest.main()
