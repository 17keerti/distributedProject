from flask import Flask, request
import requests
import time
import sys
import threading
import os

# Initialize Flask app
app = Flask(__name__)

# Topics that this subscriber is interested in
TOPICS = ["traffic"]
# Port this service runs on
PORT = 5003
# Service name for identification/logging
SERVICE_NAME = "traffic_manager"

# Mapping of broker leader IDs to their corresponding URLs
LEADER_URL_MAP = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

# Function to retrieve the URL of the current leader broker
def get_current_leader_url():
    # Iterate over all known broker URLs (excluding duplicates)
    for broker_url in set(LEADER_URL_MAP.values()):
        try:
            print(f"🔍 Trying {broker_url} for leader info...")
            res = requests.get(f"http://{broker_url}/get_leader", timeout=2)
            res.raise_for_status()
            leader_id = res.json().get("leader_id")
            print(f"📢 Leader ID found via {broker_url}: {leader_id}")
            return LEADER_URL_MAP.get(leader_id)
        except Exception as e:
            print(f"⚠️ Could not reach {broker_url}: {e}")
    print("❌ All known brokers unreachable. Retrying soon...")
    return None

# Function to continuously connect to and listen from SSE stream for a topic
def listen_to_stream(topic):
    while True:
        # Get the current leader's URL
        leader_url = get_current_leader_url()
        if not leader_url:
            time.sleep(5)  # Retry after delay if leader is unavailable
            continue

        try:
            # Construct the stream endpoint for the topic
            url = f"http://{leader_url}/stream/{topic}"
            print(f"🔌 Connecting to SSE stream for topic '{topic}' at {url}")
            response = requests.get(url, stream=True)

            # Stream and process each line
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    data = line[len("data:"):].strip()  # Extract message content
                    print(f"📥 [TRAFFIC MANAGER] Received SSE for '{topic}': {data}", flush=True)
        except Exception as e:
            print(f"⚠️ SSE connection error for topic '{topic}': {e}", flush=True)
            time.sleep(5)  # Retry after short delay if connection fails

# Entry point for the script
if __name__ == '__main__':
    # Launch a background thread for each topic
    for topic in TOPICS:
        threading.Thread(target=listen_to_stream, args=(topic,), daemon=True).start()

    print(f"🚦 Traffic Manager running on port {PORT} with SSE listener...", flush=True)

    # Start Flask app (though not currently serving any HTTP endpoints)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
