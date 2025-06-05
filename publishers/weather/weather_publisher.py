import time
import requests
from utils.lamport_clock import LamportClock

# Configuration for San Jose, CA (can be updated)
CITY = "Santa Clara"
API_URL = f"https://wttr.in/{CITY}?format=j1"
TOPIC = "weather"
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
                print(f"📢 Leader ID via {broker_url}: {leader_id}")
                return leader_id
        except Exception as e:
            print(f"⚠️ Failed to contact {broker_url}: {e}")
    return None

def get_weather_data():
    """
    Fetch weather data from wttr.in for the configured city.
    Returns a dictionary with temperature, humidity, description, and timestamps.
    """
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather_data = {
            "temperature": data['current_condition'][0]['temp_C'],
            "humidity": data['current_condition'][0]['humidity'],
            "description": data['current_condition'][0]['weatherDesc'][0]['value'],
            "timestamp": time.time(),
            "lamport_ts": clock.tick()
        }
        return weather_data
    except requests.RequestException as e:
        print(f"❌ Error fetching weather data: {e}")
        return None

def publish_weather():
    """
    Publish weather data to the current leader broker with priority.
    Severe weather gets higher priority.
    """
    weather = get_weather_data()
    if not weather:
        print("⚠️ Skipping publish due to fetch error.")
        return

    # Determine severity and assign priority
    desc = weather["description"].lower()
    severe = any(word in desc for word in [
        "storm", "thunder", "hail", "rain", "snow", "sleet",
        "mist", "fog", "overcast", "heavy", "blizzard", "wind", "ice"
    ])
    priority = 0 if severe else 2

    message = {
        "topic": TOPIC,
        "data": weather,
        "priority": priority
    }

    try:
        print("🔄 Fetching leader info...")
        leader_id = get_current_leader()
        if not leader_id:
            print("❌ Could not determine leader.")
            return

        leader_url = KNOWN_BROKERS.get(leader_id)
        if not leader_url:
            print(f"❌ Unknown leader ID: {leader_id}")
            return

        publish_url = f"http://{leader_url}/publish"
        print(f"🌐 Publishing to {publish_url}")
        print("📦 Payload:", message)

        res = requests.post(publish_url, json=message, timeout=3)
        res.raise_for_status()
        print("☁️ Published weather data successfully.")
    except Exception as e:
        print("❌ Failed to publish weather:", e)

if __name__ == "__main__":
    while True:
    # Infinite loop to publish weather data every 10 seconds
        publish_weather()
        time.sleep(10)  
