"""G1.7 local MCP host contract and process-level stdio tests.

These tests do not make live model calls.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest

from generators.foundation import Authorization, Permission
from generators.mcp_server import MCPHost, serve, MAX_INPUT_LINE
from generators.model_host import ModelOutput


class SyntheticHost:
    configured = True

    def __init__(self):
        self.calls = 0

    def generate(self, kind, brief):
        self.calls += 1
        return ModelOutput("# Synthetic model draft\n\nContent.",
                           "synthetic-fixture", "synthetic-model", "test-response")


def rpc(method, request_id=1, params=None):
    return {"jsonrpc": "2.0", "method": method,
            "id": request_id, "params": {} if params is None else params}


def granted(*permissions):
    return Authorization(frozenset(permissions))


class MCPProtocolTests(unittest.TestCase):
    def setUp(self):
        self.fake = SyntheticHost()
        self.host = MCPHost(granted(Permission.CREATE), self.fake)

    def initialize(self):
        reply = self.host.handle(rpc("initialize", params={"protocolVersion": "2025-11-25"}))
        self.assertEqual(reply["result"]["protocolVersion"], "2025-11-25")

    def test_initialize_and_list_tools(self):
        self.assertEqual(self.host.handle(rpc("tools/list"))["error"]["code"], -32002)
        self.initialize()
        tools = self.host.handle(rpc("tools/list"))["result"]["tools"]
        self.assertEqual([x["name"] for x in tools],
                         ["generate_prompt", "generate_concept", "generate_document",
                          "submit_prompt_draft", "submit_concept_draft", "submit_document_draft",
                          "generate_image_brief", "submit_image_brief",
                          "generate_design", "render_abstract_image"])
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["additionalProperties"], False)
            self.assertEqual(tool["inputSchema"]["required"],
                             ["objective", "content"] if tool["name"].startswith("submit_")
                             else ["objective"])

    def test_handshake_legacy_version(self):
        response = self.host.handle(rpc("initialize",
                            params={"protocolVersion": "2025-06-18"}))
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")

    def test_notification_never_executes(self):
        self.initialize()
        self.assertIsNone(self.host.handle(rpc("tools/call", request_id=None,
                                     params={"name": "generate_prompt",
                                             "arguments": {"objective": "Do something"}})))
        self.assertEqual(self.fake.calls, 0)

    def test_three_template_tools(self):
        self.initialize()
        for name in ("generate_prompt", "generate_concept", "generate_document"):
            with self.subTest(name=name):
                response = self.host.handle(rpc("tools/call", params={
                    "name": name, "arguments": {"objective": "Draft a plan"}}))
                data = response["result"]
                self.assertFalse(data["isError"], data)
                self.assertIn("# ", data["content"][0]["text"])
                self.assertEqual(data["structuredContent"]["state"], "reviewed")
                self.assertEqual(data["structuredContent"]["verification"]["llm_generation"], "not_run")
                self.assertFalse(data["structuredContent"]["output_verified"])
        self.assertEqual(self.fake.calls, 0)

    def test_permission_is_not_tool_argument(self):
        self.initialize()
        response = self.host.handle(rpc("tools/call", params={
            "name": "generate_prompt", "arguments": {
                "objective": "Draft", "permission": "billable_operations"}}))
        self.assertTrue(response["result"]["isError"])
        self.assertIn("INVALID_REQUEST", response["result"]["content"][0]["text"])

    def test_no_implicit_billable_permission(self):
        self.initialize()
        response = self.host.handle(rpc("tools/call", params={
            "name": "generate_document", "arguments": {
                "objective": "Draft", "mode": "model"}}))
        self.assertTrue(response["result"]["isError"])
        self.assertIn("PERMISSION_DENIED", response["result"]["content"][0]["text"])
        self.assertEqual(self.fake.calls, 0)

    def test_explicit_model_grants(self):
        host = MCPHost(granted(Permission.CREATE, Permission.EXTERNAL,
                               Permission.BILLABLE), self.fake)
        host.handle(rpc("initialize"))
        result = host.handle(rpc("tools/call", params={
            "name": "generate_document",
            "arguments": {"objective": "Draft", "mode": "model"}}))["result"]
        self.assertFalse(result["isError"], result)
        self.assertEqual(self.fake.calls, 1)
        self.assertEqual(result["structuredContent"]["verification"]["llm_generation"],
                         "host_reported")
        self.assertEqual(result["structuredContent"]["provenance"]["model_provider"],
                         "synthetic-fixture")

    def test_malformed_tool_call_and_unknown_method(self):
        self.initialize()
        self.assertEqual(self.host.handle(rpc("tools/call", params={
            "name": "delete_repository", "arguments": {}}))["error"]["code"], -32602)
        self.assertEqual(self.host.handle(rpc("unknown"))["error"]["code"], -32601)
        self.assertEqual(self.host.handle(rpc("tools/call", params={
            "name": "generate_prompt", "arguments": ["not-an-object"]}))["error"]["code"], -32602)

    def test_invalid_rpc(self):
        self.assertEqual(self.host.handle("bad")["error"]["code"], -32600)
        self.assertEqual(self.host.handle({"jsonrpc": "2.0", "method": "initialize",
                                           "id": True})["error"]["code"], -32600)

    def test_stdin_output_and_oversize(self):
        messages = [
            rpc("initialize"),
            rpc("tools/call", params={"name": "generate_prompt",
                                        "arguments": {"objective": "Draft"}}),
        ]
        source = io.BytesIO(b"".join((json.dumps(x) + "\n").encode() for x in messages))
        sink = io.BytesIO()
        serve(self.host, source, sink)
        lines = [json.loads(x) for x in sink.getvalue().splitlines()]
        self.assertEqual(len(lines), 2)
        self.assertFalse(lines[1]["result"]["isError"])
        self.assertNotIn(b"sk-", sink.getvalue())
        huge = io.BytesIO(b"x" * (MAX_INPUT_LINE + 10) + b"\n")
        sink = io.BytesIO()
        serve(self.host, huge, sink)
        self.assertEqual(json.loads(sink.getvalue())["error"]["code"], -32700)


class MCPProcessTests(unittest.TestCase):
    def run_server(self, *flags):
        messages = [rpc("initialize"),
                    rpc("tools/call", request_id=2, params={
                        "name": "generate_prompt", "arguments": {
                            "objective": "Local host smoke test"}})]
        process = subprocess.run(
            [sys.executable, "-m", "generators.mcp_server", *flags],
            input="\n".join(json.dumps(x) for x in messages) + "\n",
            capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, "")
        return [json.loads(line) for line in process.stdout.splitlines()]

    def test_deny_by_default_as_process(self):
        replies = self.run_server()
        self.assertEqual(replies[1]["id"], 2)
        self.assertTrue(replies[1]["result"]["isError"])
        self.assertIn("PERMISSION_DENIED", replies[1]["result"]["content"][0]["text"])

    def test_real_local_process_template_execution(self):
        replies = self.run_server("--allow-create")
        self.assertFalse(replies[1]["result"]["isError"])
        self.assertIn("Prompt Specification", replies[1]["result"]["content"][0]["text"])
        self.assertEqual(replies[1]["result"]["structuredContent"]["state"], "reviewed")

    def test_real_stdio_host_submissions_without_paid_provider(self):
        messages = [rpc("initialize")]
        for index, name in enumerate(("submit_prompt_draft", "submit_concept_draft",
                                      "submit_document_draft"), start=2):
            messages.append(rpc("tools/call", request_id=index, params={
                "name": name, "arguments": {
                    "objective": "Draft a local test",
                    "content": "# Host draft\n\n## Details\n\nLocal text."}}))
        proc = subprocess.run(
            [sys.executable, "-m", "generators.mcp_server", "--allow-create"],
            input="\n".join(json.dumps(x) for x in messages) + "\n",
            capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        records = [json.loads(x) for x in proc.stdout.splitlines()]
        self.assertEqual(len(records), 4)
        for record in records[1:]:
            self.assertFalse(record["result"]["isError"], record)
            details = record["result"]["structuredContent"]
            self.assertEqual(details["state"], "reviewed")
            self.assertEqual(details["verification"]["llm_generation"], "not_attested")
            self.assertEqual(details["provenance"]["model_provider"], "not-attested")

    def test_live_verifier_blocks_without_auth_or_credentials(self):
        env = dict(os.environ)
        env.pop("OPENAI_API_KEY", None)
        env.pop("INTEL_OPENAI_MODEL", None)
        for args, expected in [
            ([], "explicit authorization required"),
            (["--authorize-live-billable"], "model host not configured"),
        ]:
            with self.subTest(args=args):
                outcome = subprocess.run(
                    [sys.executable, "-m", "scripts.verify_model_live", *args],
                    capture_output=True, text=True, timeout=10,
                    check=False, env=env,
                )
                self.assertEqual(outcome.returncode, 2)
                result = json.loads(outcome.stdout)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["reason"], expected)


if __name__ == "__main__":
    unittest.main()
