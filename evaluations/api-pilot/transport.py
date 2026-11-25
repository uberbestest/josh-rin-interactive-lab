"""One bounded HTTPS request. No SDK, redirects, implicit retries, or saved key."""
from __future__ import annotations

import base64
import http.client
import ssl
import time

from common import canonical, now

HOST = "api.openai.com"
PATH = "/v1/responses"
MAX_BODY_BYTES = 4 * 1024 * 1024
SAFE_HEADERS = {"x-request-id", "content-type", "retry-after", "openai-processing-ms"}


class Transport:
    def __init__(self, api_key, organization, project, timeout=90):
        for value in (api_key, organization, project):
            if not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n"):
                raise ValueError("Credentials must be nonempty single-line values")
            try:
                value.encode("ascii")
            except UnicodeEncodeError as exc:
                raise ValueError("Credential headers must be ASCII") from exc
        self._key = api_key
        self.organization = organization
        self.project = project
        self.timeout = timeout

    def send(self, payload):
        """Return evidence even for errors; caller saves it before parsing anything."""
        envelope = {"http_status": None, "headers": {}, "body_base64": "",
                    "started_utc": now(), "ended_utc": None, "elapsed_seconds": None,
                    "error_type": None, "body_complete": False}
        started = time.monotonic()
        body = bytearray()
        connection = None
        try:
            connection = http.client.HTTPSConnection(
                HOST, timeout=self.timeout, context=ssl.create_default_context())
            connection.request("POST", PATH, body=canonical(payload).encode("utf-8"), headers={
                "Authorization": "Bearer " + self._key,
                "OpenAI-Organization": self.organization,
                "OpenAI-Project": self.project,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "JoshRinLab-native-pilot/1",
            })
            response = connection.getresponse()
            envelope["http_status"] = response.status
            envelope["headers"] = {k.lower(): v for k, v in response.getheaders()
                                   if k.lower() in SAFE_HEADERS}
            while len(body) <= MAX_BODY_BYTES:
                remaining = self.timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError("response deadline")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read(min(65536, MAX_BODY_BYTES + 1 - len(body)))
                if not chunk:
                    if getattr(response, "length", None) not in (None, 0):
                        envelope["error_type"] = "IncompleteRead"
                    else:
                        envelope["body_complete"] = True
                    break
                body.extend(chunk)
            if len(body) > MAX_BODY_BYTES:
                envelope["error_type"] = "ResponseTooLarge"
                del body[MAX_BODY_BYTES:]
        except http.client.IncompleteRead as exc:
            body.extend(exc.partial[:max(0, MAX_BODY_BYTES - len(body))])
            envelope["error_type"] = "IncompleteRead"
        except (Exception, KeyboardInterrupt) as exc:
            # Exception messages can contain request details; retain only the class.
            envelope["error_type"] = type(exc).__name__
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception as exc:
                    envelope["error_type"] = envelope["error_type"] or type(exc).__name__
                    envelope["body_complete"] = False
            envelope["body_base64"] = base64.b64encode(body).decode("ascii")
            envelope["ended_utc"] = now()
            envelope["elapsed_seconds"] = round(time.monotonic() - started, 6)
        return envelope
