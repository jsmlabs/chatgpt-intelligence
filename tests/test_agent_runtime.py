"""Offline safety and execution tests for the agent capability runtime."""
from __future__ import annotations

import unittest

from generators.agent_runtime import (
    AgentCapability, AgentRegistry, AgentRuntime, RetryableFailure,
)
from generators.foundation import Authorization, Permission


class AgentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.calls = 0
        self.now = 0.0

    def runtime(self, capability, **kwargs):
        return AgentRuntime(AgentRegistry((capability,)), observer=self.events.append,
                            sleeper=lambda seconds: setattr(self, "now", self.now + seconds),
                            clock=lambda: self.now, **kwargs)

    def test_explicit_capability_and_routing(self):
        def invoke(data):
            self.calls += 1
            return {"echo": data["message"]}
        rt = self.runtime(AgentCapability("local.echo", invoke, input_keys=frozenset({"message"})))
        result = rt.execute("local.echo", {"message": "hello"})
        self.assertTrue(result["ok"])
        self.assertFalse(result["verified"])
        self.assertEqual(result["output"], {"echo": "hello"})
        self.assertEqual(rt.execute("unknown", {})["error"]["code"], "CAPABILITY_UNAVAILABLE")
        self.assertEqual(self.calls, 1)

    def test_permission_denied_before_handler(self):
        rt = self.runtime(AgentCapability("repo.write", lambda _: self.fail("called"),
            permissions=frozenset({Permission.REPO_WRITE})))
        self.assertEqual(rt.execute("repo.write", {"permissions": ["write_repositories"]})
                         ["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(self.events[-1]["attempts"], 0)

    def test_permission_granted(self):
        rt = self.runtime(AgentCapability("repo.write", lambda _: "done",
            permissions=frozenset({Permission.REPO_WRITE})))
        self.assertTrue(rt.execute("repo.write", {},
            authorization=Authorization(frozenset({Permission.REPO_WRITE})))["ok"])

    def test_validation_before_execution(self):
        rt = self.runtime(AgentCapability("strict", lambda _: self.fail("called"),
            input_keys=frozenset({"objective"})))
        self.assertEqual(rt.execute("strict", {"unexpected": True})["error"]["code"],
                         "INVALID_REQUEST")
        self.assertEqual(rt.execute("strict", {"objective": "x"},
            deadline_seconds=0)["error"]["code"], "INVALID_REQUEST")
        self.assertEqual(self.events[-1]["attempts"], 0)

    def test_idempotent_retries_with_bounded_backoff(self):
        def invoke(data):
            self.calls += 1
            if self.calls < 3:
                raise RetryableFailure()
            return data
        rt = self.runtime(AgentCapability("read", invoke, idempotent=True, max_attempts=3))
        result = rt.execute("read", {"x": 1})
        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 3)
        self.assertAlmostEqual(self.now, 0.3)
        self.assertEqual(self.events[-1]["outcome"], "SUCCEEDED")

    def test_retry_exhaustion_and_deadline(self):
        def fail(_):
            self.calls += 1
            raise RetryableFailure()
        rt = self.runtime(AgentCapability("read", fail, idempotent=True, max_attempts=3))
        self.assertEqual(rt.execute("read", {}, deadline_seconds=0.05)
                         ["error"]["code"], "DEADLINE_EXCEEDED")
        self.assertEqual(self.calls, 1)
        self.assertEqual(rt.execute("read", {})["error"]["code"], "RETRY_EXHAUSTED")

    def test_no_retry_for_unexpected_exception(self):
        def fail(_):
            self.calls += 1
            raise RuntimeError("secret: do not leak")
        rt = self.runtime(AgentCapability("read", fail, idempotent=True, max_attempts=3))
        result = rt.execute("read", {})
        self.assertEqual(result["error"]["code"], "HANDLER_FAILED")
        self.assertNotIn("secret", str(result))
        self.assertEqual(self.calls, 1)

    def test_output_validation(self):
        for value in (object(), {"bad": object()}, float("nan"), "x" * 200):
            with self.subTest(value=type(value)):
                rt = self.runtime(AgentCapability("read", lambda _, v=value: v,
                                                  max_output_chars=128))
                self.assertEqual(rt.execute("read", {})["error"]["code"],
                                 "VALIDATION_FAILED")

    def test_observer_is_non_authoritative_and_redacted(self):
        def bad_observer(_):
            raise RuntimeError("observer failure")
        rt = AgentRuntime(AgentRegistry((AgentCapability("read", lambda _: "ok"),)),
                          observer=bad_observer)
        self.assertTrue(rt.execute("read", {"secret": "private"})["ok"])
        rt2 = self.runtime(AgentCapability("read", lambda _: "ok"))
        rt2.execute("read", {"secret": "private"})
        self.assertNotIn("private", str(self.events))

    def test_duplicate_registration_and_retry_guard(self):
        cap = AgentCapability("read", lambda _: "ok")
        with self.assertRaises(ValueError):
            AgentRegistry((cap, cap))
        with self.assertRaises(ValueError):
            AgentCapability("write", lambda _: None, max_attempts=2)
        with self.assertRaises(ValueError):
            AgentCapability("../unsafe", lambda _: None)
        with self.assertRaises(ValueError):
            AgentCapability("bad", lambda _: None, permissions=frozenset({"create"}))


if __name__ == "__main__":
    unittest.main()
