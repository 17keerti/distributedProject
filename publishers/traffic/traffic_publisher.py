import requests
import time
import random

KNOWN_BROKERS = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

TOPIC = "traffic"

def get_current_leader():
    for broker_id, broker_url in KNOWN_BROKERS.items():
        try:
            print(f"🔍 Trying {broker_url} for leader info...")
            res = requests.get(f"http://{broker_url}/get_leader", timeout=2)
            if res.status_code == 200:
                leader_id = res.json().get("leader_id")
                print(f"📢 Leader ID found via {broker_url}: {leader_id}")
                return leader_id
        except Exception as e:
            print(f"⚠️ Failed to contact {broker_url}: {e}")
    return None

while True:
    congestion = random.choice(["low", "medium", "high"])
    priority = {"low": 2, "medium": 1, "high": 0}[congestion]

    traffic_data = {
        "topic": TOPIC,
        "data": {
            "congestion": congestion,
            "accident_reported": random.choice([True, False]),
            "location": "Main St"
        },
        "priority": priority,
    }

    try:
        print("🔄 Trying to fetch leader info...")
        leader_id = get_current_leader()
        if not leader_id:
            print("❌ Could not determine leader.")
            time.sleep(10)
            continue

        leader_url = KNOWN_BROKERS.get(leader_id)
        if not leader_url:
            print("❌ Unknown leader ID:", leader_id)
            time.sleep(10)
            continue

        publish_url = f"http://{leader_url}/publish"
        print(f"➡️ Publishing to leader at {publish_url}")
        print(f"📦 Payload: {traffic_data}")

        res = requests.post(publish_url, json=traffic_data, timeout=3)
        res.raise_for_status()

        print("✅ Published traffic data successfully.")
    except Exception as e:
        print("❌ Failed to publish traffic:", e)

    time.sleep(10)
