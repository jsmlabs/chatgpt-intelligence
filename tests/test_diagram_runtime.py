"""G3.3 diagram topology, safe SVG, Mermaid, export and MCP tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree

from generators.diagram_runtime import DiagramRuntime, diagram_capability, verify_svg
from generators.foundation import Authorization, Permission
from generators.mcp_server import MCPHost

CREATE = Authorization(frozenset({Permission.CREATE}))
NODES = [{"id": "client", "label": "Web client", "type": "service"},
         {"id": "api", "label": "API & gateway", "type": "process"},
         {"id": "db", "label": "Database", "type": "database"}]
EDGES = [{"source": "client", "target": "api", "label": "request"},
         {"source": "api", "target": "db", "label": "query"}]


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.runtime = DiagramRuntime()

    def make(self, **kwargs):
        return self.runtime.execute("/INTEL GENERATE DIAGRAM", authorization=CREATE,
                                    request={"objective": "Service topology", **kwargs})

    def test_registered_and_default(self):
        self.assertEqual(diagram_capability().formats, ("json", "mermaid", "svg"))
        result = self.make()
        self.assertTrue(result["ok"], result)
        value = json.loads(result["content"])
        self.assertEqual(len(value["nodes"]), 3)
        self.assertEqual(len(value["edges"]), 2)
        self.assertEqual([n["layer"] for n in value["nodes"]], [0, 1, 2])
        self.assertEqual(result["manifest"].state.value, "reviewed")
        self.assertFalse(result["manifest"].output_verified)

    def test_svg_architecture_and_escape(self):
        nodes = [{"id": "client", "label": '<script>alert("X")</script>', "type": "service"},
                 {"id": "api", "label": "API & gateway", "type": "decision"}]
        edges = [{"source": "client", "target": "api", "label": "<query>"}]
        result = self.make(format="svg", kind="architecture", direction="LR",
                           nodes=nodes, edges=edges)
        self.assertTrue(result["ok"], result)
        svg = result["content"]
        self.assertIn("&lt;script&gt;", svg)
        self.assertNotIn("<script>", svg)
        self.assertIn("API &amp; gateway", svg)
        data = json.loads(self.make(kind="architecture", direction="LR",
                                    nodes=nodes, edges=edges)["content"])
        self.assertTrue(all(verify_svg(svg, data).values()))
        self.assertEqual(ElementTree.fromstring(svg).tag,
                         "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(result["evidence"]["browser_render"], "not_run")

    def test_mermaid_and_repeatability(self):
        a = self.make(format="mermaid", nodes=NODES, edges=EDGES)
        b = self.make(format="mermaid", nodes=NODES, edges=EDGES)
        self.assertTrue(a["ok"], a)
        self.assertEqual(a["content"], b["content"])
        self.assertIn("flowchart TB", a["content"])
        self.assertIn("client -->|request| api", a["content"])
        self.assertIn("API #amp; gateway", a["content"])
        self.assertEqual(a["evidence"]["mermaid_parser"], "not_run")

    def test_invalid_graphs_fail_closed(self):
        scenarios = [
            ({"nodes": [], "edges": []}, "INVALID_REQUEST"),
            ({"nodes": [{"id": "UP", "label": "Upper"}], "edges": []}, "INVALID_REQUEST"),
            ({"nodes": [{"id": "x", "label": "A"}, {"id": "x", "label": "B"}],
              "edges": []}, "INVALID_REQUEST"),
            ({"nodes": [{"id": "x", "label": "A"}],
              "edges": [{"source": "x", "target": "missing"}]}, "INVALID_REQUEST"),
            ({"nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
              "edges": [{"source": "a", "target": "b"},
                        {"source": "b", "target": "a"}]}, "INVALID_REQUEST"),
            ({"nodes": [{"id": "x", "label": "A"}], "edges": None}, "INVALID_REQUEST"),
            ({"kind": "mindmap"}, "INVALID_REQUEST"),
            ({"format": "pdf"}, "UNSUPPORTED_FORMAT"),
            ({"direction": "RL"}, "INVALID_REQUEST"),
            ({"accent": "javascript:alert(1)"}, "INVALID_REQUEST"),
            ({"allow_billable": True}, "INVALID_REQUEST"),
        ]
        for options, expected in scenarios:
            with self.subTest(options=str(options)[:70]):
                self.assertEqual(self.make(**options)["error"]["code"], expected)

    def test_exports_and_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for fmt, extension in (("json", "json"), ("mermaid", "mmd"), ("svg", "svg")):
                name = "diagram." + extension
                output = self.runtime.execute("/INTEL GENERATE DIAGRAM",
                    request={"objective": "Example", "format": fmt},
                    authorization=CREATE, export_root=root, filename=name)
                self.assertTrue(output["ok"], output)
                self.assertEqual(output["manifest"].state.value, "exported")
                self.assertTrue(output["manifest"].output_verified)
                self.assertEqual(output["evidence"]["file_sha256"],
                                 hashlib.sha256((root / name).read_bytes()).hexdigest())
                duplicate = self.runtime.execute("/INTEL GENERATE DIAGRAM",
                    request={"objective": "Example", "format": fmt},
                    authorization=CREATE, export_root=root, filename=name)
                self.assertEqual(duplicate["error"]["code"], "DESTINATION_EXISTS")
            for name in ("../escape.svg", "folder/diagram.svg", "invalid.png"):
                fail = self.runtime.execute("/INTEL GENERATE DIAGRAM",
                    request={"objective": "Example", "format": "svg"},
                    authorization=CREATE, export_root=root, filename=name)
                self.assertFalse(fail["ok"])
        denied = self.runtime.execute("/INTEL GENERATE DIAGRAM",
                    request={"objective": "Example"}, authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        external = self.runtime.execute("/INTEL GENERATE DIAGRAM",
                    request={"objective": "Example"}, authorization=CREATE, provider="openai-api")
        self.assertEqual(external["error"]["code"], "CAPABILITY_UNAVAILABLE")

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            cmd = [sys.executable, "-m", "generators", "diagram",
                   "--objective", "Service path", "--diagram-kind", "architecture",
                   "--node", "web|Web|service", "--node", "api|API|process",
                   "--edge", "web|api|request", "--format", "svg",
                   "--export-root", folder, "--filename", "topology.svg"]
            denied = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("PERMISSION_DENIED", denied.stderr)
            success = subprocess.run(cmd + ["--authorize-create"],
                                     capture_output=True, text=True, timeout=15)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(success.stdout, (Path(folder)/"topology.svg").read_text())

    def test_mcp_three_formats(self):
        host = MCPHost(CREATE)
        host.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        tools = host.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual(len(tools), 15)
        self.assertIn("generate_diagram", [x["name"] for x in tools])
        for fmt in ("json", "mermaid", "svg"):
            response = host.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "generate_diagram", "arguments": {
                    "objective": "Services", "format": fmt}}})["result"]
            self.assertFalse(response["isError"], response)
            self.assertEqual(response["structuredContent"]["capability"], "diagram")
            self.assertFalse(response["structuredContent"]["output_verified"])
        bad = host.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "generate_diagram", "arguments": {
                "objective": "Test", "allow_create": True}}})
        self.assertEqual(bad["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
