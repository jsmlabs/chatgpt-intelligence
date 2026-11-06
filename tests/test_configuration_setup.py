"""Schema, precedence, no-secret export, and read-only setup tests."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import intel
import intel_config as cfg


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        env = patch.dict(os.environ, {"INTEL_CONFIG_HOME": temp.name, "NO_COLOR": "1"}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = intel.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_schema_and_legacy_migration(self):
        self.assertEqual(cfg.validate({"language": "de"}), {"schema_version": 1, "language": "de"})
        for obj in ([], {"language":"fr"}, {"schema_version":2,"language":"en"},
                    {"schema_version":True}, {"language":"en","api_key":"sensitive"}):
            with self.subTest(obj=obj), self.assertRaises(cfg.ConfigError):
                cfg.validate(obj)

    def test_precedence_and_source(self):
        self.assertEqual(cfg.effective()["source"], "default")
        cfg.write_user({"language":"de"})
        self.assertEqual(cfg.effective()["language"], "de")
        self.assertEqual(cfg.effective(environ={"INTEL_LANGUAGE":"en"})["source"], "environment")
        self.assertEqual(cfg.effective(cli_language="de",environ={"INTEL_LANGUAGE":"en"})["source"], "cli")
        with self.assertRaises(cfg.ConfigError):
            cfg.effective(environ={"INTEL_LANGUAGE":"invalid"})

    def test_setup_preview_apply_idempotent(self):
        self.assertEqual(self.cli("setup")[0], 0)
        self.assertFalse(cfg.config_path().exists())
        self.assertEqual(self.cli("--json", "setup", "--apply")[0], 0)
        content = cfg.config_path().read_bytes()
        self.assertEqual(self.cli("--json", "setup", "--apply")[0], 0)
        self.assertEqual(cfg.config_path().read_bytes(), content)
        self.assertEqual(self.cli("--json", "config", "validate")[0], 0)

    def test_set_language_with_env_override(self):
        self.assertEqual(self.cli("config","language","de")[0],0)
        with patch.dict(os.environ,{"INTEL_LANGUAGE":"en"}):
            self.assertEqual(intel.read_language(),"en")
            self.assertEqual(json.loads(self.cli("--json","config","show")[1])["source"],"environment")
        self.assertEqual(intel.read_language(),"de")

    def test_export_import_preview_and_refusal_to_overwrite(self):
        cfg.write_user({"language":"de"})
        output = self.root / "public.json"
        self.assertEqual(self.cli("config","export",str(output))[0],0)
        self.assertEqual(json.loads(output.read_text())["language"],"de")
        self.assertEqual(self.cli("config","export",str(output))[0],3)
        cfg.write_user({"language":"en"})
        self.assertEqual(self.cli("config","import",str(output))[0],0)
        self.assertEqual(cfg.read_user()["language"],"en")
        self.assertEqual(self.cli("config","import",str(output),"--apply")[0],0)
        self.assertEqual(cfg.read_user()["language"],"de")

    def test_secret_rejection_and_invalid_files(self):
        sample = self.root / "bad.json"
        sample.write_text('{"language":"en","token":"sk-sensitive"}')
        self.assertEqual(self.cli("config","import",str(sample),"--apply")[0],3)
        self.assertNotIn("sk-sensitive", self.cli("config","import",str(sample))[2])
        sample.write_text('{"language":"en","language":"de"}')
        self.assertEqual(self.cli("config","import",str(sample))[0],3)
        sample.write_bytes(b"x"*9000)
        self.assertEqual(self.cli("config","import",str(sample))[0],3)

    def test_symlinks_and_permission_failures(self):
        real = self.root / "original.json"
        real.write_text('{"language":"en"}')
        link = self.root / "alias.json"
        try:
            link.symlink_to(real)
        except (OSError, NotImplementedError):
            self.skipTest("No symlink support")
        self.assertEqual(self.cli("config","import",str(link),"--apply")[0],3)
        self.assertEqual(self.cli("config","export",str(link))[0],3)
        self.assertEqual(real.read_text(),'{"language":"en"}')

    def test_setup_invalid_existing_config_is_not_overwritten(self):
        cfg.config_path().write_text('{"language":"de","secret":"keep"}')
        original = cfg.config_path().read_bytes()
        self.assertEqual(self.cli("setup","--apply")[0],3)
        self.assertEqual(cfg.config_path().read_bytes(),original)

    def test_noninteractive_and_json(self):
        self.assertEqual(self.cli("--non-interactive","setup")[0],0)
        self.assertFalse(cfg.config_path().exists())
        self.assertEqual(self.cli("--json","config","show")[0],0)
        self.assertEqual(self.cli("config","import","missing.json","--apply")[0],3)


if __name__ == "__main__":
    unittest.main()
