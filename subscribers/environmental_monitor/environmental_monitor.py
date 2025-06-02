from flask import Flask
import requests
import time
import threading
from utils.lamport_clock import LamportClock
import json

# Initialize Flask app
app = Flask(__name__)

# Topics to subscribe to
TOPICS = ["weather", "air_quality"]
# Port for this subscriber service
PORT = 5004
# Name identifier for this service
SERVICE_NAME = "environmental_monitor"

# Mapping from broker ID to its URL
LEADER_URL_MAP = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

# Instantiate a Lamport clock for causal ordering
clock = LamportClock()

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

# Function to connect to the SSE stream and listen for messages
def listen_to_stream(topic):
    while True:
        # Fetch the latest leader broker
        leader_url = get_current_leader_url()
        if not leader_url:
            time.sleep(5)  # Retry after some delay if leader is not available
            continue

        try:
            url = f"http://{leader_url}/stream/{topic}"
            print(f"🔌 Connecting to SSE stream for topic '{topic}' at {url}")
            response = requests.get(url, stream=True)

            # Read stream line by line
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    raw_data = line[len("data:"):].strip()
                    try:
                        json_data = json.loads(raw_data)
                        lamport_ts = json_data["data"].get("lamport_ts")

                        # Update Lamport clock
                        if lamport_ts is not None:
                            clock.receive(lamport_ts)
                        else:
                            clock.tick()

                        print(
                            f"📥 [ENVIRONMENTAL MONITOR] Received SSE for '{topic}': {raw_data} | Lamport Clock: {clock.get_time()}",
                            flush=True
                        )
                    except Exception as err:
                        print(f"❌ Error decoding message: {err}", flush=True)
        except Exception as e:
            print(f"⚠️ SSE connection error for topic '{topic}': {e}", flush=True)
            time.sleep(5)  # Wait before retrying

# Main entry point
if __name__ == '__main__':
    # Start a separate thread for each topic's SSE listener
    for topic in TOPICS:
        threading.Thread(target=listen_to_stream, args=(topic,), daemon=True).start()

    print(f"🌍 Environmental Monitor running on port {PORT} with SSE listener...", flush=True)
    
    # Start Flask app (not serving HTTP endpoints but required for long-running service)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
