import unittest
import requests
import json
import time

BROKER_URL = "http://localhost:5003"  # Adjust if needed

class TestBroker(unittest.TestCase):

    def test_health_check(self):
        """Test the broker's health check endpoint."""
        response = requests.get(f"{BROKER_URL}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OK")

    def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing to a topic."""

        topic = "traffic"
        subscribe_url = f"{BROKER_URL}/subscribe"
        unsubscribe_url = f"{BROKER_URL}/unsubscribe"
        
        # Subscribe
        subscribe_payload = {"topic": topic, "mode": "webhook", "url": "http://example.com/webhook"}  #Dummy URL
        subscribe_response = requests.post(subscribe_url, json=subscribe_payload)
        self.assertEqual(subscribe_response.status_code, 200)
        self.assertIn("Subscribed", subscribe_response.json()["message"])

        # Unsubscribe
        unsubscribe_payload = {"topic": topic, "mode": "webhook", "url": "http://example.com/webhook"}
        unsubscribe_response = requests.post(unsubscribe_url, json=unsubscribe_payload)
        self.assertEqual(unsubscribe_response.status_code, 200)
        self.assertIn("Unsubscribed", unsubscribe_response.json()["message"])

    def test_publish_message(self):
        """Test publishing a message to a topic."""

        topic = "test_publish_topic"
        publish_url = f"{BROKER_URL}/publish"
        publish_payload = {"topic": topic, "data": {"message": "Hello, world!"}, "priority": "high"}
        publish_response = requests.post(publish_url, json=publish_payload)
        self.assertEqual(publish_response.status_code, 200)

    def test_view_logs(self):
        """Test viewing logs for a topic."""
        topic = "test_log_topic"
        publish_url = f"{BROKER_URL}/publish"
        log_url = f"{BROKER_URL}/logs/{topic}"

        # Publish a message
        payload = {"topic": topic, "data": {"message": "Hello logs!"}, "priority": "high"}
        publish_response = requests.post(publish_url, json=payload)
        self.assertEqual(publish_response.status_code, 200)

        # Give broker time to process
        time.sleep(1)

        # Fetch logs
        log_response = requests.get(log_url)
        self.assertEqual(log_response.status_code, 200)

        logs = log_response.json().get("logs", [])
        self.assertTrue(len(logs) > 0, "Expected at least one log entry")
        self.assertIn("Hello logs!", str(logs))


if __name__ == '__main__':
    unittest.main()