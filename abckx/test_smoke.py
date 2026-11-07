"""Readiness regression: Docker can reset sockets before Authelia listens."""
import importlib.util
import io
import pathlib
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("image_smoke", pathlib.Path(__file__).with_name("image-smoke.py"))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class ReadinessTest(unittest.TestCase):
    def test_retry_connection_reset_until_real_http_response(self):
        self.assertTrue(hasattr(smoke, "wait_for_login"), "readiness must handle connection resets")
        response = io.BytesIO(b"<html>ready</html>")
        with patch.object(smoke.urllib.request, "urlopen", side_effect=[ConnectionResetError(), response]) as request:
            with patch.object(smoke.time, "sleep"):
                html = smoke.wait_for_login("http://127.0.0.1:9091/", Mock(poll=Mock(return_value=None)))
        self.assertEqual("<html>ready</html>", html)
        self.assertEqual(2, request.call_count)

    def test_exited_runtime_fails_instead_of_retrying(self):
        self.assertTrue(hasattr(smoke, "wait_for_login"), "readiness must detect process failure")
        with patch.object(smoke.urllib.request, "urlopen", side_effect=ConnectionResetError()):
            with self.assertRaises(RuntimeError):
                smoke.wait_for_login("http://127.0.0.1:9091/", Mock(poll=Mock(return_value=1)))
