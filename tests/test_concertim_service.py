import unittest
from unittest.mock import Mock, patch
from concertim.concertim_service import ConcertimService

class TestConcertimService(unittest.TestCase):
    def setUp(self):
        self.service = ConcertimService()

    def test_authenticate(self):
        # Test successful authentication
        self.assertTrue(self.service._authenticate())
        self.assertIsNotNone(self.service._auth_token)

        # Test authentication failure
        with patch("keystoneauth1.session.Session", side_effect=Exception):
            self.assertFalse(self.service._authenticate())
            self.assertIsNone(self.service._auth_token)

    def test_build_query(self):
        # Test query building with a single metric and filter
        device_id = "123"
        metrics = [{"name": "cpu_util", "filter": {"<=": {"foo": 5}}}]
        expected_query = {"=": {"device_id": device_id, "cpu_util": {"<=": {"foo": 5}}}}
        self.assertEqual(self.service._build_query(device_id, metrics), expected_query)

        # Test query building with multiple metrics and filters
        device_id = "456"
        metrics = [
            {"name": "cpu_util", "filter": {"<=": {"foo": 5}}},
            {"name": "disk_usage", "filter": {"==": {"bar": "baz"}}},
        ]
        expected_query = {
            "=": {
                "device_id": device_id,
                "cpu_util": {"<=": {"foo": 5}},
                "disk_usage": {"==": {"bar": "baz"}},
            }
        }
        self.assertEqual(self.service._build_query(device_id, metrics), expected_query)

    @patch("requests.post")
    def test_send_metrics(self, mock_post):
        device_id = "123"
        device_data = {"metrics": [{"name": "cpu_util", "filter": {"<=": {"foo": 5}}}]}

        # Test successful metric sending
        mock_post.return_value.status_code = 200
        self.service._send_metrics()
        mock_post.assert_called_with(
            "https://example.com/api/concertim",
            headers={"X-Auth-Token": self.service._auth_token, "Content-Type": "application/json"},
            json={
                "device_id": device_id,
                "metrics": [{"name": "cpu_util", "values": []}]
            },
        )

        # Test failed metric sending
        mock_post.return_value.status_code = 500
        self.service._send_metrics()
        mock_post.assert_called_with(
            "https://example.com/api/concertim",
            headers={"X-Auth-Token": self.service._auth_token, "Content-Type": "application/json"},
            json={
                "device_id": device_id,
                "metrics": [{"name": "cpu_util", "values": []}]
            },
        )

    def test_handle_exception(self):
        # Test handling of exception
        with self.assertLogs(level="ERROR") as logs:
            self.service._handle_exception(Exception("test error"))
            self.assertIn("test error", logs.output[0])

