from flask import Flask, jsonify
import requests
import time
import threading

# Initialize Flask app
app = Flask(__name__)
PORT = 5004  # Port on which this service will run

# List of topics this public interface listens to
TOPICS = ["air_quality", "traffic", "weather"]
SERVICE_NAME = "public_interface"

# Mapping from broker ID to the corresponding service URL
LEADER_URL_MAP = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

# Dictionary to store the latest data for each topic
latest_data = {}

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

# Function to establish an SSE connection to a topic stream and update local state
def listen_to_stream(topic):
    while True:
        # Get the current leader to connect to
        leader_url = get_current_leader_url()
        if not leader_url:
            time.sleep(5)  # Retry after a delay if no leader found
            continue

        try:
            url = f"http://{leader_url}/stream/{topic}"
            print(f"🔌 Connecting to SSE stream for topic '{topic}' at {url}")
            response = requests.get(url, stream=True)

            # Read Server-Sent Events line by line
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    data = line[len("data:"):].strip()
                    print(f"📥 [PUBLIC INTERFACE] SSE Update for '{topic}': {data}", flush=True)

                    # Store the latest data for this topic
                    latest_data[topic] = data
        except Exception as e:
            print(f"⚠️ SSE connection error for topic '{topic}': {e}", flush=True)
            time.sleep(5)  # Wait before retrying if connection fails

# HTTP endpoint to retrieve the latest data for all topics
@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(latest_data)

# Main entry point to start the service
if __name__ == '__main__':
    # Start a listener thread for each topic
    for topic in TOPICS:
        threading.Thread(target=listen_to_stream, args=(topic,), daemon=True).start()

    print(f"🌍 Public Interface running on port {PORT} with SSE listeners...", flush=True)
    
    # Run the Flask web server
    app.run(host='0.0.0.0', port=PORT, threaded=True)
