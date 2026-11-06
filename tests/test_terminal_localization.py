"""Phase 02 CLI presentation and localization regressions; no network."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import intel
from intel_console import Console, ansi_supported, cell_width, truncate
from intel_locales import CATALOGS, tr

class TerminalLocalization(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        ctx = patch.dict(os.environ, {"INTEL_CONFIG_HOME":tmp.name,"NO_COLOR":"1"})
        ctx.start()
        self.addCleanup(ctx.stop)

    def run_cli(self,*args):
        out,err = io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err):
            try:
                rc = intel.main(list(args))
            except SystemExit as exc:
                rc = exc.code if isinstance(exc.code, int) else 1
        return rc,out.getvalue(),err.getvalue()

    def test_catalog_coverage_and_fallback(self):
        self.assertEqual(set(CATALOGS["en"]), set(CATALOGS["de"]))
        self.assertTrue(all(CATALOGS["de"].values()))
        self.assertEqual(tr("fr","invalid"),"Invalid choice.")
        self.assertEqual(tr("de","nonexistent"),"nonexistent")

    def test_language_help_and_config(self):
        self.assertEqual(self.run_cli("config","language","de")[0],0)
        self.assertIn("Befehle",self.run_cli("help")[1])
        self.assertIn("Lokale Voraussetzungen",self.run_cli("help")[1])
        self.assertIn("Verwendung",self.run_cli("config","language","invalid")[2])
        doctor_code, _, doctor_error = self.run_cli("doctor", "oops")
        self.assertEqual(doctor_code, 2)
        self.assertIn("Entwicklerwerkzeug", doctor_error)
        self.assertIn("doctor [basic|full]", doctor_error)
        self.assertIn("Offline-orientierte",self.run_cli("--help")[1])
        self.assertEqual(json.loads(self.run_cli("--json","config","language","show")[1]),{"language":"de"})

    def test_inspection_json_is_clean_and_stable(self):
        for name in ("help","version","providers","doctor","status"):
            rc,out,err = self.run_cli("--json",name)
            self.assertEqual((rc,err),(0,""))
            self.assertIsInstance(json.loads(out),dict)
            self.assertNotIn("\x1b",out)
        self.assertEqual(self.run_cli("--json","generate","prompt")[0],2)
        self.assertEqual(self.run_cli("--quiet","test")[0],2)

    def test_plain_text_and_accessible_numbered_menu(self):
        stream = io.StringIO()
        console = Console(language="de",stream=stream)
        console.emit("OK","pass")
        self.assertIn("[PASS] OK",stream.getvalue())
        self.assertFalse(ansi_supported(stream))
        with patch("sys.stdin") as stdin,patch.object(console,"ask",return_value="2"):
            stdin.isatty.return_value = False
            self.assertEqual(intel.choose_menu(console,("status","doctor")),"doctor")
        self.assertIn("Diagnose",stream.getvalue())

    def test_arrow_navigation_and_confirmation_gate(self):
        console = Console(language="en",stream=io.StringIO())
        console.color = True
        with patch("sys.stdin") as stdin,patch("intel.read_key",side_effect=["down","enter"]):
            stdin.isatty.return_value = True
            self.assertEqual(intel.choose_menu(console,("status","doctor")),"doctor")
        with patch.object(console,"ask",side_effect=["prompt","Example","n"]):
            self.assertEqual(intel.interactive_generate(console),2)
        with patch.object(console,"ask",side_effect=["prompt","Example","yes"]),patch("intel.dispatch",return_value=0) as called:
            self.assertEqual(intel.interactive_generate(console),0)
            called.assert_called_once_with("generate",["prompt","--objective","Example","--authorize-create"],console)

    def test_width_and_unicode(self):
        out = io.StringIO()
        console = Console(language="de",stream=out)
        with patch.object(Console,"width",property(lambda self:36)):
            console.table([("Diagnoseprüfung","A very long explanation with lots of details","warn")])
        self.assertTrue(all(cell_width(line)<=36 for line in out.getvalue().splitlines()))
        self.assertLessEqual(cell_width(truncate("Überprüfung",7)),7)

    def test_explicit_generator_authority_unchanged(self):
        rc,_,err = self.run_cli("generate","prompt","--objective","Example")
        self.assertEqual(rc,2)
        self.assertIn("PERMISSION_DENIED",err)

if __name__ == "__main__":
    unittest.main()
