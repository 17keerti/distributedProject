import requests
import time
import random
from utils.lamport_clock import LamportClock  # Importing LamportClock for logical timestamping

# Known broker addresses mapped by broker ID
KNOWN_BROKERS = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

TOPIC = "traffic"  # The topic this publisher sends data to
clock = LamportClock()  # Initialize Lamport clock

def get_current_leader():
    """
    Query all known brokers to determine the current leader.
    Returns the broker ID of the leader if found, else None.
    """
    for broker_id, broker_url in KNOWN_BROKERS.items():
        try:
            print(f"🔍 Trying {broker_url} for leader info...")
            # Call each broker's /get_leader endpoint
            res = requests.get(f"http://{broker_url}/get_leader", timeout=2)
            if res.status_code == 200:
                leader_id = res.json().get("leader_id")  # Extract leader ID
                print(f"📢 Leader ID found via {broker_url}: {leader_id}")
                return leader_id
        except Exception as e:
            print(f"⚠️ Failed to contact {broker_url}: {e}")  # Connection failure
    return None  # If no leader could be found

def publish_traffic():
    """
    Simulates a traffic event and publishes it to the leader broker 
    with priority and Lamport timestamp.
    """
    # Simulate congestion level and corresponding priority
    congestion = random.choice(["low", "medium", "high"])  # Random traffic condition
    priority = {"low": 2, "medium": 1, "high": 0}[congestion]  # Lower value = higher priority

    clock.tick()  # Advance Lamport clock for the event

    # Construct the traffic data payload
    traffic_data = {
        "topic": TOPIC,
        "data": {
            "congestion": congestion,
            "accident_reported": random.choice([True, False]),  # Randomly simulate accident
            "location": "Main St",  # Static location for this simulation
            "lamport_ts": clock.get_time()  # Logical timestamp
        },
        "priority": priority,  # Include message priority
    }

    try:
        print("🔄 Trying to fetch leader info...")
        leader_id = get_current_leader()  # Discover the leader
        if not leader_id:
            print("❌ Could not determine leader.")
            return

        leader_url = KNOWN_BROKERS.get(leader_id)  # Get URL of current leader
        if not leader_url:
            print("❌ Unknown leader ID:", leader_id)
            return

        publish_url = f"http://{leader_url}/publish"  # Leader's /publish endpoint
        print(f"➡️ Publishing to leader at {publish_url}")
        print(f"📦 Payload: {traffic_data}")

        res = requests.post(publish_url, json=traffic_data, timeout=3)  # Send POST request
        res.raise_for_status()  # Raise error if request failed

        print("✅ Published traffic data successfully.")
    except Exception as e:
        print("❌ Failed to publish traffic:", e)  # Handle connection or request errors

if __name__ == "__main__":
    # Loop forever, publishing a traffic event every 10 seconds
    while True:
        publish_traffic()
        time.sleep(10)
