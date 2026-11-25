import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gateway


class DownstreamTests(unittest.TestCase):
    def setUp(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(folder) / 'incremental-response.json'
        self.payload = {'job_id': 'job-test', 'trace_id': 'trace-test'}
        self.enterContext(patch.object(gateway, 'log'))
        self.enterContext(patch.object(gateway.time, 'sleep'))

    def test_connection_refused_is_retried_three_times(self):
        with patch.object(gateway.opener, 'open', side_effect=URLError(ConnectionRefusedError())) as send:
            with self.assertRaises(gateway.DownstreamFailure) as failure:
                gateway.role_call('echecker', self.payload, self.path)
        self.assertEqual(send.call_count, 3)
        self.assertEqual(failure.exception.details['code'], 'DOWNSTREAM_UNAVAILABLE')
        self.assertEqual(failure.exception.details['stage'], 'incremental-check')
        self.assertEqual(json.loads(self.path.read_text()), failure.exception.details)

    def test_timeout_after_request_is_never_retried(self):
        with patch.object(gateway.opener, 'open', side_effect=TimeoutError) as send:
            with self.assertRaises(gateway.DownstreamFailure) as failure:
                gateway.role_call('echecker', self.payload, self.path)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(failure.exception.details['code'], 'DOWNSTREAM_TIMEOUT')

    def test_reported_upstream_timeout_is_classified(self):
        response = HTTPError('http://echecker/', 422, 'failure', {}, io.BytesIO(b'{"error_code":"TIMEOUT"}'))
        with patch.object(gateway.opener, 'open', side_effect=response) as send:
            with self.assertRaises(gateway.DownstreamFailure) as failure:
                gateway.role_call('echecker', self.payload, self.path)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(failure.exception.details['code'], 'DOWNSTREAM_TIMEOUT')

    def test_recovery_during_connection_retry_returns_success(self):
        with patch.object(gateway.opener, 'open', side_effect=[
            URLError(ConnectionRefusedError()), io.BytesIO(b'{"status":"SUCCEEDED"}'),
        ]) as send:
            result = gateway.role_call('echecker', self.payload, self.path)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(result, json.loads(self.path.read_text()))


if __name__ == '__main__':
    unittest.main()
