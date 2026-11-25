import base64
import http.client
import io
import ssl
import unittest
from unittest.mock import patch

from common import canonical
from transport import Transport


class Response:
    status = 200

    def __init__(self, body=b'{"output":[]}'):
        self.body = body

    def getheaders(self):
        return [("X-Request-ID", "request-1"), ("Authorization", "must-not-be-recorded")]

    def read(self, size):
        result, self.body = self.body[:size], self.body[size:]
        return result


class Connection:
    instances = []

    def __init__(self, host, timeout, context):
        self.host, self.timeout, self.context = host, timeout, context
        self.sock = None
        self.response = Response()
        self.requests = []
        self.closed = False
        self.instances.append(self)

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class TransportTests(unittest.TestCase):
    def setUp(self):
        Connection.instances = []

    @patch("transport.http.client.HTTPSConnection", Connection)
    def test_exact_request_and_safe_evidence(self):
        payload = {"input": [{"role": "user", "content": "café 🦆"}]}
        evidence = Transport("test-secret", "org-lab", "proj-lab").send(payload)
        connection = Connection.instances[0]
        method, path, body, headers = connection.requests[0]
        self.assertEqual((connection.host, method, path), ("api.openai.com", "POST", "/v1/responses"))
        self.assertEqual(body, canonical(payload).encode("utf-8"))
        self.assertEqual(headers["Authorization"], "Bearer test-secret")
        self.assertEqual(connection.context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(connection.context.check_hostname)
        self.assertEqual(evidence["headers"], {"x-request-id": "request-1"})
        self.assertNotIn("test-secret", canonical(evidence))
        self.assertTrue(evidence["body_complete"])
        self.assertTrue(connection.closed)
        self.assertEqual(base64.b64decode(evidence["body_base64"]), b'{"output":[]}')

    def test_timeout_never_retries_or_exposes_exception_message(self):
        class TimeoutConnection(Connection):
            def getresponse(self):
                raise TimeoutError("test-secret")
        with patch("transport.http.client.HTTPSConnection", TimeoutConnection):
            evidence = Transport("test-secret", "org-lab", "proj-lab").send({})
        self.assertEqual(len(Connection.instances), 1)
        self.assertEqual(evidence["error_type"], "TimeoutError")
        self.assertFalse(evidence["body_complete"])
        self.assertNotIn("test-secret", canonical(evidence))

    def test_http_redirect_is_recorded_never_followed(self):
        class Redirect(Connection):
            def getresponse(self):
                self.response.status = 307
                return self.response
        with patch("transport.http.client.HTTPSConnection", Redirect):
            evidence = Transport("secret", "org", "proj").send({})
        self.assertEqual(evidence["http_status"], 307)
        self.assertEqual(len(Connection.instances), 1)

    def test_partial_response_retained(self):
        class Partial(Connection):
            def getresponse(self):
                class Broken(Response):
                    def read(self, size):
                        raise http.client.IncompleteRead(b'partial', 20)
                return Broken()
        with patch("transport.http.client.HTTPSConnection", Partial):
            evidence = Transport("secret", "org", "proj").send({})
        self.assertEqual(base64.b64decode(evidence["body_base64"]), b'partial')
        self.assertEqual(evidence["error_type"], "IncompleteRead")

    def test_response_size_bound(self):
        class Large(Connection):
            def getresponse(self):
                return Response(b"123456")
        with patch("transport.http.client.HTTPSConnection", Large), patch("transport.MAX_BODY_BYTES", 4):
            evidence = Transport("secret", "org", "proj").send({})
        self.assertEqual(base64.b64decode(evidence["body_base64"]), b"1234")
        self.assertEqual(evidence["error_type"], "ResponseTooLarge")
        self.assertFalse(evidence["body_complete"])

    def test_header_injection_rejected_before_network(self):
        with self.assertRaises(ValueError):
            Transport("secret\r\nX: 1", "org", "proj")

    def test_declared_content_length_truncation_is_uncertain(self):
        class Socket:
            def makefile(self, _mode):
                return io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\n{}')
        class Truncated(Connection):
            def getresponse(self):
                response = http.client.HTTPResponse(Socket())
                response.begin()
                return response
        with patch("transport.http.client.HTTPSConnection", Truncated):
            evidence = Transport("secret", "org", "proj").send({})
        self.assertEqual(base64.b64decode(evidence["body_base64"]), b'{}')
        self.assertEqual(evidence["error_type"], "IncompleteRead")
        self.assertFalse(evidence["body_complete"])

    def test_keyboard_interrupt_preserves_received_evidence(self):
        class Interrupted(Connection):
            def getresponse(self):
                class Body(Response):
                    def read(self, size):
                        if self.body:
                            data, self.body = self.body, b''
                            return data
                        raise KeyboardInterrupt()
                return Body(b'received-before-interrupt')
        with patch("transport.http.client.HTTPSConnection", Interrupted):
            evidence = Transport("secret", "org", "proj").send({})
        self.assertEqual(base64.b64decode(evidence["body_base64"]), b'received-before-interrupt')
        self.assertEqual(evidence["http_status"], 200)
        self.assertEqual(evidence["headers"]["x-request-id"], "request-1")
        self.assertEqual(evidence["error_type"], "KeyboardInterrupt")
        self.assertFalse(evidence["body_complete"])


if __name__ == "__main__":
    unittest.main()
