"""Forge Studio v3.2 interoperability contract against this repository's real MCP host.

Tests local stdio protocol, discovery and permissions; does NOT assert installed
ChatGPT connector, external tunnel, paid provider or Forge Studio package health.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest


class ForgeInteropTests(unittest.TestCase):
    def test_stdio_protocol_discovery_and_offline_handoff(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                        "clientInfo": {"name": "forge-studio", "version": "3.2.0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "generate_prompt", "arguments": {
                 "objective": "Offline Forge interoperability", "provider": "template"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
             "params": {"name": "generate_prompt", "arguments": {
                 "objective": "Do not grant provider permissions", "mode": "model"}}},
        ]
        env = dict(os.environ)
        env.pop("OPENAI_API_KEY", None)
        env.pop("INTEL_OPENAI_MODEL", None)
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "generators.mcp_server", "--allow-create"],
            input="".join(json.dumps(x) + "\n" for x in requests),
            capture_output=True, text=True, timeout=15, check=False, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        replies = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([reply["id"] for reply in replies], [1, 2, 3, 4])
        self.assertIn(replies[0]["result"]["protocolVersion"], ("2025-11-25", "2025-06-18"))
        self.assertEqual(replies[0]["result"]["serverInfo"]["name"], "chatgpt-intelligence")
        names = {t["name"] for t in replies[1]["result"]["tools"]}
        self.assertIn("generate_prompt", names)
        self.assertIn("submit_prompt_draft", names)
        self.assertNotIn("generate_image_comfyui", names)
        self.assertFalse(replies[2]["result"]["isError"])
        artifact = replies[2]["result"]["structuredContent"]
        self.assertEqual(artifact["state"], "reviewed")
        self.assertEqual(artifact["verification"]["structural_validation"], "passed")
        self.assertTrue(replies[3]["result"]["isError"])
        self.assertIn("PERMISSION_DENIED", replies[3]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
