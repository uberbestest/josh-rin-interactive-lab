"""Real pinned SDK, mock HTTP only. Missing SDK is an installation error.

Run with the requirements-sdk.txt environment. Every socket connection fails.
"""
import contextlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx2 as httpx
from openai import OpenAI

import runner
from test_regressions import manifest, usage


class SDKTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(importlib.metadata.version("openai"), runner.SDK_VERSION)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = manifest()
        self.requests = []
        self.assignment = -1
        self.mode = "happy"
        self.patch_socket = patch.object(socket.socket, "connect", side_effect=AssertionError("No network"))
        self.patch_socket.start()
        self.addCleanup(self.patch_socket.stop)
        self.http_client = httpx.Client(transport=httpx.MockTransport(self.handle))
        self.client = OpenAI(api_key="OFFLINE_AUDIT_SENTINEL", http_client=self.http_client,
                             max_retries=0, timeout=90)
        self.addCleanup(self.client.close)

    def handle(self, request):
        payload = json.loads(request.content)
        self.requests.append(payload)
        if self.mode == "timeout":
            raise httpx.ReadTimeout("offline ambiguous response", request=request)
        if self.mode == "error":
            return httpx.Response(429, json={"error": {"message": "offline enforced limit",
                                  "type": "rate_limit_error", "code": "project_spend_limit_exceeded"}},
                                  headers={"x-request-id": "offline-error-id"})
        if self.mode == "invalid_json":
            return httpx.Response(200, text="not JSON", headers={"content-type": "application/json"})
        if len(payload["input"]) == 1:
            self.assignment += 1
            self.fixture = runner.DryResponseClient(self.manifest["cases"][self.assignment % 4])
        response = self.fixture.create()
        response.update(object="response", created_at=0, model=payload["model"],
                        parallel_tool_calls=False, tool_choice="auto", tools=runner.TOOLS,
                        service_tier="default", usage=usage())
        for item in response["output"]:
            item.update(id=f"offline-item-{len(self.requests)}", status="completed")
            if item["type"] == "message":
                item.update(role="assistant", phase="final_answer")
                item["content"][0]["annotations"] = []
        response["output"].insert(0, {"id": f"offline-r-{len(self.requests)}", "type": "reasoning",
                                     "summary": [], "encrypted_content": "offline-encrypted"})
        if self.mode == "missing_usage":
            response["usage"] = None
        return httpx.Response(200, json=response, headers={"x-request-id": "offline-response-id"})

    def execute(self):
        return runner.execute(self.manifest, runner.canonical(self.manifest).encode(), True,
                              self.client, self.root / "archive")

    def first_trace(self):
        path = self.root / "archive" / "A-precommitted_combined__gpt-6-astra.jsonl"
        return [json.loads(s) for s in path.read_text().splitlines()]

    def test_full_matrix_real_sdk_serialization_and_history(self):
        summary = self.execute()
        self.assertEqual(len(self.requests), 48)
        self.assertEqual(summary["safe_joint_completions"], 8)
        self.assertEqual(summary["error_assignments"], 0)
        self.assertTrue(all(p["service_tier"] == "default" and p["store"] is False
                            and p["parallel_tool_calls"] is False for p in self.requests))
        continuations = [p for p in self.requests if len(p["input"]) > 1]
        self.assertEqual(len(continuations), 40)
        for payload in continuations:
            self.assertEqual(payload["input"][-1]["type"], "function_call_output")
            self.assertTrue(any(item.get("encrypted_content") for item in payload["input"]))
        events = self.first_trace()
        requests = [e for e in events if e["event"] == "request"]
        responses = [e for e in events if e["event"] == "provider_response"]
        self.assertEqual(len(requests), len(responses))
        for sent, received in zip(requests, responses):
            self.assertEqual(json.loads(received["wire_request_body"]), sent["payload"])
            self.assertEqual(received["headers"]["x-request-id"], "offline-response-id")
        self.assertNotIn("OFFLINE_AUDIT_SENTINEL", "\n".join(p.read_text() for p in (self.root / "archive").glob("*.json*")))
        self.assertEqual(runner.verify_archive(self.root / "archive")["verified_assignments"], 8)

    def test_sdk_timeout_has_no_retries_or_later_dispatch(self):
        self.mode = "timeout"
        summary = self.execute()
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(summary["provider_attempted_requests"], 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        exception = next(e for e in self.first_trace() if e["event"] == "request_exception")
        self.assertEqual(json.loads(exception["wire_request_body"]), self.requests[0])

    def test_sdk_http_error_body_is_preserved(self):
        self.mode = "error"
        summary = self.execute()
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(summary["provider_responses"], 1)
        self.assertEqual(summary["model_responses"], 0)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        error = next(e for e in self.first_trace() if e["event"] == "request_exception")
        self.assertEqual(json.loads(error["body"])["error"]["code"], "project_spend_limit_exceeded")
        self.assertEqual(error["headers"]["x-request-id"], "offline-error-id")
        completed = next(e for e in self.first_trace() if e["event"] == "case_complete")
        self.assertFalse(completed["result"]["scientific_model_participant"])

    def test_sdk_missing_usage_preserves_entire_response(self):
        self.mode = "missing_usage"
        summary = self.execute()
        self.assertEqual(len(self.requests), 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        raw = next(e for e in self.first_trace() if e["event"] == "provider_response")
        self.assertIsNone(json.loads(raw["body"])["usage"])

    def test_sdk_invalid_response_preserved_before_parsing(self):
        self.mode = "invalid_json"
        summary = self.execute()
        self.assertEqual(len(self.requests), 1)
        self.assertIsNone(summary["estimated_provider_cost_usd"])
        raw = next(e for e in self.first_trace() if e["event"] == "provider_response")
        self.assertEqual(raw["body"], "not JSON")

    def test_cli_live_guard_prevents_second_mock_run(self):
        self.assert_cli_guard(0, 48, "COMPLETED_REVIEW_REQUIRED")

    def test_cli_uncertainty_retains_guard_across_launches(self):
        self.mode = "timeout"
        self.assert_cli_guard(2, 1, "RECONCILIATION_REQUIRED")

    def assert_cli_guard(self, exit_code, requests, status):
        local = self.root / "source"
        local.mkdir()
        for name in ("runner.py", "manifest.json", "README.md", "requirements-sdk.txt"):
            shutil.copyfile(runner.HERE / name, local / name)
        from subprocess import CompletedProcess
        clean = CompletedProcess([], 0, stdout="", stderr="")

        def make_client(**kwargs):
            self.assertEqual(kwargs["base_url"], runner.API_BASE)
            self.assertEqual(kwargs["organization"], "offline-org")
            self.assertEqual(kwargs["project"], "offline-project")
            self.assertEqual(kwargs["max_retries"], 0)
            return OpenAI(**kwargs, http_client=self.http_client)

        argv = ["runner.py", "--live", "--confirm-live", "YES", "--output", str(local / "results" / "cli-run")]
        with patch.object(runner, "HERE", local), patch.object(runner.subprocess, "run", return_value=clean), \
             patch("openai.OpenAI", side_effect=make_client), \
             patch.dict(os.environ, {"OPENAI_API_KEY": "OFFLINE_AUDIT_SENTINEL",
                                     "OPENAI_ORG_ID": "offline-org", "OPENAI_PROJECT_ID": "offline-project"}), \
             patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(), exit_code)
            self.assertEqual(len(self.requests), requests)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                runner.main()
            self.assertEqual(len(self.requests), requests)
        marker = json.loads((local / "results" / ".live-run.json").read_text())
        self.assertEqual(marker["status"], status)


if __name__ == "__main__":
    unittest.main()
