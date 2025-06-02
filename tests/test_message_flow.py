import unittest
import requests
import time

BROKER_URL = "http://localhost:5003"  # Update if broker runs on different port

class TestMessageFlow(unittest.TestCase):

    def test_publish_message(self):
        """Test publishing a message to a topic."""
        url = f"{BROKER_URL}/publish"
        payload = {
            "topic": "traffic",
            "data": {"congestion": "high"},
            "priority": "high"
        }
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 200)

    def test_get_leader(self):
        """Test getting current leader."""
        url = f"{BROKER_URL}/get_leader"
        response = requests.get(url)
        self.assertIn(response.status_code, [200, 503])  # May be 503 if no leader
        if response.status_code == 200:
            self.assertIn("leader_id", response.json())

if __name__ == '__main__':
    unittest.main()
