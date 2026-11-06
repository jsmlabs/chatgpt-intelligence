"""Explicit local Ollama smoke test. No cloud fallback and no billable calls.

Runs one local generation each for PROMPT and DOCUMENT by default.
Outputs only bounded structural evidence; not generated text or private inputs.
"""
from __future__ import annotations

import argparse
import json
import sys

from generators import Authorization, OllamaLocalHost, Permission, ProviderRouter, TextRuntime


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify local Ollama generators")
    parser.add_argument("--authorize-local-inference", action="store_true",
                        help="Explicitly allow one local Ollama inference per selected type")
    parser.add_argument("--types", nargs="+", choices=("PROMPT", "CONCEPT", "DOCUMENT"),
                        default=["PROMPT", "DOCUMENT"])
    parser.add_argument("--model-timeout", type=float, default=60.0)
    parser.add_argument("--model-max-output-tokens", type=int, default=4096)
    args = parser.parse_args(argv)
    if not args.authorize_local_inference:
        print(json.dumps({"status": "BLOCKED", "reason": "explicit local authorization required"}))
        return 2
    if (not 1 <= args.model_timeout <= 120 or
            not 128 <= args.model_max_output_tokens <= 8192):
        parser.error("Local timeout must be 1-120 seconds and tokens 128-8192")
    host = OllamaLocalHost(timeout=args.model_timeout,
                           max_output_tokens=args.model_max_output_tokens)
    if not host.configured:
        print(json.dumps({"status": "BLOCKED", "reason": "local model not configured"}))
        return 2
    if not host.available():
        print(json.dumps({"status": "BLOCKED", "reason": "local model not installed or reachable"}))
        return 2
    runtime = TextRuntime(provider_router=ProviderRouter(ollama_host=host))
    grants = Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL}))
    results = []
    for kind in dict.fromkeys(args.types):
        outcome = runtime.execute(
            "/INTEL GENERATE " + kind,
            request={"objective": "Create a concise fictional local software design example",
                     "audience": "Software engineers",
                     "constraints": ["Use Markdown headings and specific actionable sections"]},
            authorization=grants, provider="ollama-local",
        )
        if not outcome["ok"]:
            results.append({"type": kind, "status": "FAILED",
                            "error_code": outcome["error"]["code"]})
            continue
        manifest = outcome["manifest"]
        results.append({"type": kind, "status": "PASSED",
                        "provider": manifest.provenance.get("model_provider"),
                        "state": manifest.state.value,
                        "structurally_valid": all(manifest.validations.values()),
                        "balanced_code_fences": manifest.validations.get("balanced_code_fences"),
                        "human_reviewed": False, "source_verified": False})
    success = len(results) == len(set(args.types)) and all(
        entry["status"] == "PASSED" for entry in results)
    print(json.dumps({"status": "PASSED" if success else "FAILED",
                      "local_model_attempted": True, "results": results}, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
