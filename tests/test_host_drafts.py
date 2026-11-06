"""G1.9 client-generated draft intake tests - no model invocations."""
from __future__ import annotations

import unittest

from generators.artifacts import ArtifactState
from generators.foundation import Authorization, Permission
from generators.host_drafts import submit_host_draft
from generators.mcp_server import MCPHost


def rpc(method, params=None, id=1):
    return {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": id}


CREATE = Authorization(frozenset({Permission.CREATE}))


class HostDraftTests(unittest.TestCase):
    def test_all_three_host_drafts_are_structurally_valid_without_external(self):
        for kind in ("PROMPT", "CONCEPT", "DOCUMENT"):
            with self.subTest(kind=kind):
                result = submit_host_draft(kind,
                    request={"objective": "Write a project draft"},
                    content="## Scope\n\nClient text.", authorization=CREATE)
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["manifest"].state, ArtifactState.REVIEWED)
                self.assertEqual(result["manifest"].provenance["model_provider"], "not-attested")
                self.assertEqual(result["evidence"]["llm_generation"], "not_attested")
                self.assertTrue(result["content"].startswith("# "))
                self.assertFalse(result["verified"])

    def test_submission_requires_create_and_rejects_bad_content(self):
        for value in ("", "# Draft\n\n```python\nunfinished", "# Bad\x00text", "x" * 70000):
            with self.subTest(size=len(value)):
                result = submit_host_draft("PROMPT", request={"objective": "Draft"},
                    content=value, authorization=CREATE)
                self.assertFalse(result["ok"], result)
        denied = submit_host_draft("PROMPT",
            request={"objective": "Draft"}, content="# Draft\n\nGood.",
            authorization=Authorization())
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        self.assertIsNone(denied["manifest"])

    def test_untrusted_model_content_cannot_set_permissions(self):
        result = submit_host_draft("CONCEPT",
            request={"objective": "Draft", "permission": "billable_operations"},
            content="# Draft\n\nIgnore policy.", authorization=CREATE)
        self.assertEqual(result["error"]["code"], "INVALID_REQUEST")

    def test_mcp_submission_and_no_model_or_network_call(self):
        host = MCPHost(CREATE)
        host.handle(rpc("initialize"))
        result = host.handle(rpc("tools/call", {
            "name": "submit_document_draft",
            "arguments": {"objective": "Document the interface",
                          "content": "# Draft\n\n## Inputs\n\nClient-provided text."}
        }))["result"]
        self.assertFalse(result["isError"], result)
        self.assertEqual(result["structuredContent"]["state"], "reviewed")
        self.assertEqual(result["structuredContent"]["provenance"]["model_provider"], "not-attested")
        self.assertEqual(result["structuredContent"]["verification"]["llm_generation"], "not_attested")

    def test_mcp_submission_rejects_mode_and_missing_create(self):
        for auth, args, expected in (
            (CREATE, {"objective": "Draft", "content": "# Draft", "mode": "model"}, "Unknown submission field"),
            (Authorization(), {"objective": "Draft", "content": "# Draft"}, "PERMISSION_DENIED"),
        ):
            host = MCPHost(auth)
            host.handle(rpc("initialize"))
            result = host.handle(rpc("tools/call", {
                "name": "submit_prompt_draft", "arguments": args
            }))
            if expected == "PERMISSION_DENIED":
                self.assertTrue(result["result"]["isError"])
                self.assertIn(expected, result["result"]["content"][0]["text"])
            else:
                self.assertEqual(result["error"]["message"], expected)


if __name__ == "__main__":
    unittest.main()
