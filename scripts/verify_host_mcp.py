"""Verify the real stdio MCP handoff with synthetic drafts only.

No model, cloud service, or billable call is made.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

SUBMISSIONS = ("submit_prompt_draft", "submit_concept_draft", "submit_document_draft")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G1.9 local MCP handoff smoke")
    parser.add_argument("--authorize-local-create", action="store_true")
    args = parser.parse_args(argv)
    if not args.authorize_local_create:
        print(json.dumps({"status": "BLOCKED", "reason": "explicit authorization required"}))
        return 2
    frames = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
               "params": {"protocolVersion": "2025-11-25"}}]
    for index, name in enumerate(SUBMISSIONS, 2):
        frames.append({"jsonrpc": "2.0", "id": index, "method": "tools/call",
                       "params": {"name": name, "arguments": {
                           "objective": "Synthetic local integration test",
                           "content": "# Synthetic draft\n\n## Scope\n\nNo model was called."}}})
    try:
        process = subprocess.run(
            [sys.executable, "-m", "generators.mcp_server", "--allow-create"],
            input="\n".join(json.dumps(frame) for frame in frames) + "\n",
            capture_output=True, text=True, timeout=15, check=False)
        if process.returncode or process.stderr.strip():
            raise ValueError("Process failure")
        messages = [json.loads(line) for line in process.stdout.splitlines()]
        if len(messages) != 4 or "result" not in messages[0]:
            raise ValueError("Invalid MCP handshake")
        results = []
        for name, frame in zip(SUBMISSIONS, messages[1:]):
            response = frame.get("result", {})
            meta = response.get("structuredContent", {})
            ok = (response.get("isError") is False and meta.get("state") == "reviewed"
                  and meta.get("verification", {}).get("llm_generation") == "not_attested"
                  and meta.get("provenance", {}).get("model_provider") == "not-attested")
            results.append({"tool": name, "status": "PASSED" if ok else "FAILED"})
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError):
        print(json.dumps({"status": "FAILED", "reason": "local MCP check failed"}))
        return 1
    status = "PASSED" if all(item["status"] == "PASSED" for item in results) else "FAILED"
    print(json.dumps({"status": status, "chatgpt_client_connected": False,
                      "paid_provider_invoked": False, "results": results}, sort_keys=True))
    return 0 if status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
