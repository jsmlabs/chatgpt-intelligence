"""Phase 05 passive capability registry and routing boundary regressions."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import intel
from generators.capabilities import (
    GENERATORS, GENERATOR_NAMES, capability_report, generators_report, providers_report,
)
from generators.foundation import Authorization, Permission, default_registry
from generators.provider_router import ProviderRouter


class ConfiguredHost:
    configured = True
    def available(self):
        raise AssertionError("Passive discovery must never probe")
    def generate(self, *_):
        raise AssertionError("Discovery must never generate")


class RegistryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env = patch.dict(os.environ, {"INTEL_CONFIG_HOME": tmp.name, "NO_COLOR": "1"})
        env.start()
        self.addCleanup(env.stop)

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = intel.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_exact_implemented_cli_types_vs_planned_types(self):
        self.assertEqual(len(GENERATOR_NAMES), 10)
        self.assertEqual(len(default_registry().all()), 16)
        self.assertEqual(tuple(GENERATORS), GENERATOR_NAMES)
        self.assertNotIn("video", GENERATORS)
        self.assertTrue(all(s.default_format in s.formats for s in GENERATORS.values()))
        self.assertTrue(all(s.permission == Permission.CREATE for s in GENERATORS.values()))

    def test_discovery_is_passive_does_not_grant_permissions(self):
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")), \
             patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            data = capability_report(ProviderRouter(ollama_host=ConfiguredHost()))
        self.assertFalse(data["permissions_are_grants"])
        self.assertEqual(data["execution_verification"], "not_run")
        self.assertEqual(data["providers"]["ollama-local"]["state"], "configured_unverified")
        self.assertFalse(data["providers"]["ollama-local"]["authorized"])
        self.assertEqual(data["providers"]["openai-api"]["state"], "not_configured")
        self.assertFalse(data["generators"]["slides"]["execution_verified"])

    def test_authorization_projections_are_not_dispatch(self):
        create = Authorization(frozenset({Permission.CREATE}))
        paid = Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL, Permission.BILLABLE}))
        router = ProviderRouter(openai_host=ConfiguredHost(), ollama_host=ConfiguredHost())
        simple = providers_report(router, create)
        enabled = providers_report(router, paid)
        self.assertFalse(simple["openai-api"]["authorized"])
        self.assertFalse(simple["ollama-local"]["authorized"])
        self.assertTrue(enabled["openai-api"]["authorized"])
        self.assertTrue(enabled["ollama-local"]["authorized"])
        self.assertFalse(enabled["openai-api"]["verified"])

    def test_cli_json_contract_and_plain_format(self):
        for command in ("capabilities", "generators", "providers"):
            code, raw, err = self.cli("--json", command)
            self.assertEqual((code, err), (0, ""), command)
            parsed = json.loads(raw)
            self.assertTrue(parsed)
            self.assertNotIn("\x1b", raw)
        self.assertEqual(len(json.loads(self.cli("--json", "generators")[1])), 10)
        self.assertIn("template", json.loads(self.cli("--json", "providers")[1]))
        self.assertIn("capabilities", self.cli("help")[1])
        self.assertEqual(self.cli("capabilities", "invalid")[0], 2)

    def test_legacy_denial_and_default_offline(self):
        rc, _, err = self.cli("generate", "prompt", "--objective", "Draft")
        self.assertEqual(rc, 2)
        self.assertIn("PERMISSION_DENIED", err)
        self.assertEqual(self.cli("generate", "prompt", "--objective", "Draft",
                                  "--provider", "openai-api", "--authorize-create")[0], 2)

    def test_generator_registry_is_immutable(self):
        with self.assertRaises(TypeError):
            GENERATORS["fake"] = GENERATORS["prompt"]

if __name__ == "__main__":
    unittest.main()
