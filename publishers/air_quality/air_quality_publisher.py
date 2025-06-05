import time
import requests
from utils.lamport_clock import LamportClock

# Configuration for San Jose, CA (can be updated)
LAT, LON = 37.3541, -121.9552
AIR_QUALITY_URL = (
    f"https://air-quality-api.open-meteo.com/v1/air-quality?"
    f"latitude={LAT}&longitude={LON}&hourly=pm10,carbon_monoxide,ozone"
)

TOPIC = "air_quality"
clock = LamportClock()

# Known broker endpoints
KNOWN_BROKERS = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

def get_current_leader():
    """
    Query all known brokers to determine the current leader.
    Returns the broker ID of the leader if found, else None.
    """
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

def get_air_quality_data():
    """
    Fetch current air quality data from Open-Meteo.
    Returns a dictionary with metrics and Lamport timestamp.
    """
    try:
        response = requests.get(AIR_QUALITY_URL)
        response.raise_for_status()
        data = response.json()

        latest = {
            "timestamp": time.time(),
            "pm10": data["hourly"]["pm10"][0],
            "carbon_monoxide": data["hourly"]["carbon_monoxide"][0],
            "ozone": data["hourly"]["ozone"][0],
            "lamport_ts": clock.tick()
        }
        return latest
    except requests.RequestException as e:
        print(f"❌ Error fetching air quality data: {e}")
        return None

def publish_air_quality():
    """
    Publish air quality data to the leader broker with appropriate priority.
    """
    air_data = get_air_quality_data()
    if air_data:
        # Determine severity and assign priority
        pm10 = air_data["pm10"]
        co = air_data["carbon_monoxide"]
        ozone = air_data["ozone"]
        severe = pm10 > 80 or co > 5 or ozone > 180
        priority = 0 if severe else 2

        message = {
            "topic": TOPIC,
            "data": air_data,
            "priority": priority
        }

        try:
            print("🔄 Trying to fetch leader info...")
            leader_id = get_current_leader()
            if not leader_id:
                print("❌ Could not determine leader.")
                return

            leader_url = KNOWN_BROKERS.get(leader_id)
            if not leader_url:
                print("❌ Unknown leader ID:", leader_id)
                return

            publish_url = f"http://{leader_url}/publish"
            print(f"➡️ Publishing to leader at {publish_url}")
            print(f"📦 Payload: {message}")

            response = requests.post(publish_url, json=message)
            response.raise_for_status()

            print("🌫️ Published air quality data successfully.")
        except Exception as e:
            print("❌ Failed to publish air data:", e)
    else:
        print("⚠️ Skipping publish due to fetch error.")

if __name__ == "__main__":
    while True:
        publish_air_quality()
        # Publish every 10 seconds
        time.sleep(10)  