
import time
import requests
import random
from lamport_clock import LamportClock

TOPIC = "weather"
BROKER_URL = "http://localhost:5001/publish"
DURATION = 180  # seconds
start_time = time.time()

clock = LamportClock()

def generate_data():
    clock.tick()  # increment on internal event
    return {
        "description": random.choice(["Sunny", "Cloudy", "Rainy"]),
        "humidity": str(random.randint(30, 90)),
        "temperature": str(random.randint(15, 35)),
        "timestamp": clock.get_time()
    }

print(f"🚀 Weather publisher with Lamport clock started at {BROKER_URL} on topic '{TOPIC}'")

while time.time() - start_time < DURATION:
    msg = {
        "topic": TOPIC,
        "priority": random.choice([1, 2]),
        "data": generate_data()
    }
    try:
        requests.post(BROKER_URL, json=msg)
    except Exception as e:
        print("⚠️ Failed to publish:", e)
    time.sleep(0.05)  # 20 messages per second

print("✅ Finished weather publishing.")
