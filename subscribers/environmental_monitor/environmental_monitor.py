from flask import Flask
import requests
import time
import threading
from utils.lamport_clock import LamportClock
import json

app = Flask(__name__)

TOPICS = ["weather", "air_quality"]
PORT = 5004
SERVICE_NAME = "environmental_monitor"
KNOWN_BROKER = "broker:5001"  # Known broker to ask for the current leader

LEADER_URL_MAP = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

# Instantiate Lamport clock
clock = LamportClock()

def get_current_leader_url():
    try:
        print("🔍 Fetching current leader...")
        res = requests.get(f"http://{KNOWN_BROKER}/get_leader", timeout=2)
        res.raise_for_status()
        leader_id = res.json().get("leader_id")
        print("📢 Leader ID:", leader_id)
        return LEADER_URL_MAP.get(leader_id)
    except Exception as e:
        print("⚠️ Failed to get leader:", e)
        return None

def listen_to_stream(topic):
    while True:
        leader_url = get_current_leader_url()
        if not leader_url:
            time.sleep(5)
            continue

        try:
            url = f"http://{leader_url}/stream/{topic}"
            print(f"🔌 Connecting to SSE stream for topic '{topic}' at {url}")
            response = requests.get(url, stream=True)

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    raw_data = line[len("data:"):].strip()
                    try:
                        json_data = json.loads(raw_data)
                        lamport_ts = json_data["data"].get("lamport_ts")
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
            time.sleep(5)

if __name__ == '__main__':
    for topic in TOPICS:
        threading.Thread(target=listen_to_stream, args=(topic,), daemon=True).start()
    print(f"🌍 Environmental Monitor running on port {PORT} with SSE listener...", flush=True)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
