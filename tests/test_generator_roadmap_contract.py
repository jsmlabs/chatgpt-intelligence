"""Keep the generator roadmap aligned with the actual local CLI catalog.

This checks documented capability availability, not live rendering or provider access.
"""
from __future__ import annotations

from pathlib import Path
import unittest

from generators.capabilities import GENERATORS

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "GENERATOR-ROADMAP.md"

DOCUMENTED = {
    "PROMPT / CONCEPT / DOCUMENT": ("prompt", "concept", "document"),
    "IMAGE (G2.1)": ("image",),
    "DESIGN": ("design",),
    "THEME": ("theme",),
    "BRAND": ("brand",),
    "GIF / Motion": ("gif",),
    "SLIDES": ("slides",),
    "DIAGRAM": ("diagram",),
}
PLANNED = {"chart", "code", "video", "audio", "workflow", "pack"}


class GeneratorRoadmapContractTests(unittest.TestCase):
    def test_implemented_capabilities_are_documented_once(self):
        content = ROADMAP.read_text(encoding="utf-8")
        section = content.split("## Verified implementation matrix", 1)[1].split("\n## ", 1)[0]
        rows = {
            cells[0].strip(): cells[1:]
            for line in section.splitlines()
            if line.startswith("| ") and not line.startswith("| ---")
            for cells in [line.strip().strip("|").split("|")]
        }
        self.assertEqual(set(DOCUMENTED) | {
            "CHART / CODE / VIDEO / AUDIO / WORKFLOW / PACK", "Capability"
        }, set(rows))
        documented = [name for group in DOCUMENTED.values() for name in group]
        self.assertEqual(len(documented), len(set(documented)))
        self.assertEqual(set(documented), set(GENERATORS))
        for label, names in DOCUMENTED.items():
            self.assertTrue(rows[label], label)
            for name in names:
                self.assertTrue(GENERATORS[name].formats, name)

    def test_planned_capabilities_are_not_advertised_as_implemented(self):
        self.assertFalse(PLANNED.intersection(GENERATORS))
        content = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("CHART / CODE / VIDEO / AUDIO / WORKFLOW / PACK", content)
        self.assertIn("No local CLI generator claimed", content)


if __name__ == "__main__":
    unittest.main()
