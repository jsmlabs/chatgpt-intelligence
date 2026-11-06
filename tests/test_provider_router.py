"""G1.8 provider routing regression and boundary tests; no real network."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from generators import (
    Authorization, Permission, TextRuntime, ProviderRouter, OllamaLocalHost,
    ToolDeclaration, ToolResolver, default_registry,
)
from generators.model_host import ModelOutput

CREATE = Authorization(frozenset({Permission.CREATE}))
LOCAL = Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL}))
PAID = Authorization(frozenset({Permission.CREATE, Permission.EXTERNAL, Permission.BILLABLE}))


class Fake:
    configured = True
    def __init__(self):
        self.calls = 0
        self.reachable = True
    def available(self):
        return self.reachable
    def generate(self, kind, brief):
        self.calls += 1
        return ModelOutput("# Draft\n\nSynthetic text.", "synthetic", "test", "")


class Response:
    def __init__(self, obj):
        self.raw = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, limit):
        return self.raw[:limit]


class ProviderRoutingTests(unittest.TestCase):
    def run_case(self, runtime, authorization=CREATE, provider=None, mode="template"):
        return runtime.execute("/INTEL GENERATE PROMPT",
            request={"objective": "Draft"}, authorization=authorization,
            provider=provider, mode=mode)

    def test_template_remains_default_and_registry_size(self):
        fake = Fake()
        rt = TextRuntime(provider_router=ProviderRouter(openai_host=fake))
        self.assertEqual(len(default_registry().all()), 16)
        result = self.run_case(rt)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["evidence"]["llm_generation"], "not_run")
        self.assertEqual(fake.calls, 0)

    def test_paid_explicit_only_and_legacy_mode(self):
        fake = Fake()
        rt = TextRuntime(provider_router=ProviderRouter(openai_host=fake))
        for grant in (CREATE, LOCAL):
            self.assertEqual(self.run_case(rt, grant, "openai-api")["error"]["code"],
                             "PERMISSION_DENIED")
        self.assertTrue(self.run_case(rt, PAID, "openai-api")["ok"])
        self.assertTrue(self.run_case(rt, PAID, mode="model")["ok"])
        self.assertEqual(fake.calls, 2)
        self.assertEqual(self.run_case(rt, PAID, "ollama-local", "model")
                         ["error"]["code"], "INVALID_REQUEST")

    def test_local_not_billable_and_reachability(self):
        local = Fake()
        rt = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        self.assertEqual(self.run_case(rt, CREATE, "ollama-local")
                         ["error"]["code"], "PERMISSION_DENIED")
        self.assertTrue(self.run_case(rt, LOCAL, "ollama-local")["ok"])
        self.assertEqual(local.calls, 1)
        local.reachable = False
        self.assertEqual(self.run_case(rt, LOCAL, "ollama-local")
                         ["error"]["code"], "TOOL_UNAVAILABLE")
        self.assertEqual(local.calls, 1)

    def test_chatgpt_requires_attested_host(self):
        host = Fake()
        rt = TextRuntime(provider_router=ProviderRouter(chatgpt_host=host))
        self.assertEqual(self.run_case(rt, CREATE, "chatgpt-host")
                         ["error"]["code"], "TOOL_UNAVAILABLE")
        tools = ToolResolver({"chatgpt-host": ToolDeclaration(
            "chatgpt-host", frozenset({"PROMPT"}), reachable=True, verified=True)})
        rt = TextRuntime(provider_router=ProviderRouter(chatgpt_host=host, host_tools=tools))
        self.assertTrue(self.run_case(rt, CREATE, "chatgpt-host")["ok"])
        self.assertEqual(host.calls, 1)

    def test_passive_detection_never_probes(self):
        local = Fake()
        with patch.object(local, "available", side_effect=AssertionError("network call")):
            data = ProviderRouter(ollama_host=local).detect(CREATE)
        self.assertTrue(data["template"]["authorized"])
        self.assertFalse(data["ollama-local"]["authorized"])
        self.assertFalse(data["chatgpt-host"]["configured"])
        self.assertFalse(data["openai-api"]["configured"])

    def test_request_cannot_select_provider(self):
        result = TextRuntime().execute("/INTEL GENERATE PROMPT",
            request={"objective": "Draft", "provider": "openai-api"},
            authorization=CREATE)
        self.assertEqual(result["error"]["code"], "INVALID_REQUEST")

    def test_loopback_model_probe_and_generate(self):
        local = OllamaLocalHost(model="test-model:latest")
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = [
                Response({"models": [{"name": "test-model:latest"}]}),
                Response({"done": True, "response": "# Draft\n\nLocal."}),
            ]
            self.assertTrue(local.available())
            from generators.artifacts import GenerationRequest
            result = local.generate("PROMPT", GenerationRequest("Draft", "Developers"))
            req = opener.return_value.open.call_args.args[0]
            self.assertEqual(req.full_url, "http://127.0.0.1:11434/api/generate")
            payload = json.loads(req.data)
            self.assertEqual(payload["stream"], False)
            self.assertEqual(result.provider, "ollama-local")
        self.assertFalse(OllamaLocalHost(model="").configured)


    def test_prose_model_output_gets_heading_and_real_provenance(self):
        local = Fake()
        local.generate = lambda kind, brief: ModelOutput(
            "Local architecture with a dashboard and component boundaries.",
            "ollama-local", "test", "")
        rt = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        result = rt.execute("/INTEL GENERATE CONCEPT",
            request={"objective": "Dashboard"}, authorization=LOCAL,
            provider="ollama-local")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["content"].startswith("# Concept Brief\n\nLocal architecture"))
        self.assertIn("\n\n## Provenance and limitations\n\n", result["content"])
        self.assertTrue(all(result["manifest"].validations.values()))

    def test_fenced_model_markdown_is_unwrapped(self):
        local = Fake()
        local.generate = lambda kind, brief: ModelOutput(
            "```markdown\n# Dashboard\n\n## Scope\n\nContent.\n```",
            "ollama-local", "test", "")
        rt = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        result = self.run_case(rt, LOCAL, "ollama-local")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["content"].startswith("# Dashboard\n\n## Scope\n"))
        self.assertNotIn("```", result["content"])

    def test_bad_model_output_still_fails_validation(self):
        local = Fake()
        rt = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        for content in ("", "# Heading\x00unsafe", "x" * 70000):
            with self.subTest(length=len(content)):
                local.generate = lambda kind, brief, value=content: ModelOutput(
                    value, "ollama-local", "test", "")
                result = self.run_case(rt, LOCAL, "ollama-local")
                self.assertEqual(result["error"]["code"], "VALIDATION_FAILED")
                self.assertEqual(result["manifest"].state.value, "failed")


    def test_open_outer_markdown_fence_from_live_concept_is_repaired(self):
        local = Fake()
        local.generate = lambda kind, brief: ModelOutput(
            "```markdown\n# AI-Native Dashboard Design - Draft\n\n"
            "## I. Core Principles\n\n- Data-first architecture.",
            "ollama-local", "gemma3:4b", "")
        runtime = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        result = runtime.execute(
            "/INTEL GENERATE CONCEPT",
            request={"objective": "Design a modern AI-native dashboard"},
            authorization=LOCAL, provider="ollama-local")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["content"].startswith("# AI-Native Dashboard Design - Draft\n"))
        self.assertNotIn("```markdown", result["content"])
        self.assertIn("\n\n## Provenance and limitations\n\n", result["content"])
        self.assertTrue(result["manifest"].validations["balanced_code_fences"])

    def test_nested_or_unclosed_code_fences_fail_closed(self):
        inputs = (
            "# Draft\n\n```python\nprint('unsafe unfinished block')",
            "```markdown\n# Draft\n\n```python\nprint('ambiguous')",
            "# Draft\n\n~~~json\n{}",
        )
        for output in inputs:
            with self.subTest(output=output[:24]):
                local = Fake()
                local.generate = lambda kind, brief, text=output: ModelOutput(
                    text, "ollama-local", "fixture", "")
                runtime = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
                result = runtime.execute(
                    "/INTEL GENERATE DOCUMENT",
                    request={"objective": "Draft"}, authorization=LOCAL,
                    provider="ollama-local")
                self.assertFalse(result["ok"], result)
                self.assertEqual(result["error"]["code"], "VALIDATION_FAILED")
                self.assertFalse(result["manifest"].validations["balanced_code_fences"])

    def test_balanced_inner_code_fence_is_preserved(self):
        local = Fake()
        local.generate = lambda kind, brief: ModelOutput(
            "# Prompt\n\nExample:\n\n```python\nprint('ok')\n```",
            "ollama-local", "fixture", "")
        runtime = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        result = runtime.execute(
            "/INTEL GENERATE PROMPT", request={"objective": "Draft"},
            authorization=LOCAL, provider="ollama-local")
        self.assertTrue(result["ok"], result)
        self.assertIn("```python\nprint('ok')\n```", result["content"])
        self.assertTrue(result["manifest"].validations["balanced_code_fences"])

    def test_closed_outer_markdown_with_inner_fences_does_not_get_corrupted(self):
        local = Fake()
        local.generate = lambda kind, brief: ModelOutput(
            "```markdown\n# Draft\n\n```python\nprint('code')\n```\n```",
            "ollama-local", "fixture", "")
        runtime = TextRuntime(provider_router=ProviderRouter(ollama_host=local))
        result = runtime.execute(
            "/INTEL GENERATE PROMPT", request={"objective": "Draft"},
            authorization=LOCAL, provider="ollama-local")
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["code"], "VALIDATION_FAILED")

    def test_no_implicit_openai_from_cli(self):
        import os, subprocess, sys
        env = dict(os.environ)
        env.pop("OPENAI_API_KEY", None)
        env.pop("INTEL_OPENAI_MODEL", None)
        result = subprocess.run(
            [sys.executable, "-m", "generators", "prompt",
             "--objective", "Offline", "--authorize-create"],
            capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
