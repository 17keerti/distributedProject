import unittest
import requests
import time
import threading
import json

BROKER_URL = "http://localhost:5003"  # Adjust if needed

class TestPubSub(unittest.TestCase):

    def test_publish_and_receive(self):
        """Test publishing a message and verifying it's logged by the broker."""

        topic = "test_pubsub_topic"
        publish_url = f"{BROKER_URL}/publish"
        log_url = f"{BROKER_URL}/logs/{topic}"

        # Publish a message
        publish_payload = {"topic": topic, "data": {"message": "Test message"}, "priority": "high"}
        publish_response = requests.post(publish_url, json=publish_payload)
        self.assertEqual(publish_response.status_code, 200)

        # Allow time for the broker to process (this might need adjustment)
        time.sleep(1)

        # Retrieve logs and verify the message
        log_response = requests.get(log_url)
        self.assertEqual(log_response.status_code, 200)
        logs = log_response.json()["logs"]
        self.assertTrue(any(log["data"]["message"] == "Test message" for log in logs))

    def test_publish_multiple_subscribers(self):
        """Test publishing to a topic with multiple subscribers."""

        topic = "test_multi_sub_topic"
        publish_url = f"{BROKER_URL}/publish"
        log_url = f"{BROKER_URL}/logs/{topic}"
        subscribe_url = f"{BROKER_URL}/subscribe"

        # Dummy subscriber URLs (replace with actual test subscribers if you have them)
        subscriber_urls = ["http://example.com/sub1", "http://example.com/sub2"]

        # Subscribe
        for url in subscriber_urls:
            subscribe_payload = {"topic": topic, "mode": "webhook", "url": url}
            requests.post(subscribe_url, json=subscribe_payload)

        # Publish a message
        publish_payload = {"topic": topic, "data": {"message": "Multi-sub message"}, "priority": "low"}
        publish_response = requests.post(publish_url, json=publish_payload)
        self.assertEqual(publish_response.status_code, 200)

        time.sleep(1) # Allow time for processing

        #Check logs (crude way to verify publish)
        log_response = requests.get(log_url)
        self.assertEqual(log_response.status_code, 200)
        logs = log_response.json()["logs"]
        self.assertTrue(any(log["data"]["message"] == "Multi-sub message" for log in logs))

if __name__ == '__main__':
    unittest.main()