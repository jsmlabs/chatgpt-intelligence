"""Explicit opt-in authenticated smoke verification of the three text generators.

Never run this from CI. No API key, model, or raw generated content is printed.
Each run requests three potentially billable model responses.
"""
from __future__ import annotations

import argparse
import json
import sys

from generators import Authorization, Permission, TextRuntime, OpenAIResponsesHost


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-live-billable", action="store_true",
                        help="Explicitly approve THREE potentially billable API requests")
    args = parser.parse_args(argv)
    if not args.authorize_live_billable:
        print(json.dumps({"status": "BLOCKED", "reason": "explicit authorization required"}))
        return 2
    host = OpenAIResponsesHost()
    if not host.configured:
        print(json.dumps({"status": "BLOCKED", "reason": "model host not configured"}))
        return 2
    runtime = TextRuntime(model_host=host)
    grant = Authorization(frozenset({
        Permission.CREATE, Permission.EXTERNAL, Permission.BILLABLE,
    }))
    report = []
    for kind in ("PROMPT", "CONCEPT", "DOCUMENT"):
        result = runtime.execute(
            "/INTEL GENERATE " + kind, mode="model",
            request={"objective": "Create a concise fictional software engineering example",
                     "audience": "Developers"},
            authorization=grant,
        )
        if not result["ok"]:
            report.append({"type": kind, "status": "FAILED",
                           "error_code": result["error"]["code"]})
            break
        manifest = result["manifest"]
        report.append({
            "type": kind, "status": "PASSED",
            "state": manifest.state.value,
            "provider": manifest.provenance.get("model_provider"),
            "response_id_present": bool(manifest.provenance.get("response_id")),
            "structurally_valid": all(manifest.validations.values()),
            "source_verified": False, "human_reviewed": False,
        })
    success = len(report) == 3 and all(x["status"] == "PASSED" for x in report)
    print(json.dumps({"status": "PASSED" if success else "FAILED",
                      "live_model_attempted": True, "results": report}, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
