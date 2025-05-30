import json
import time
import requests

# Configs
LAT, LON = 37.3541, -121.9552
AIR_QUALITY_URL = (
    f"https://air-quality-api.open-meteo.com/v1/air-quality?"
    f"latitude={LAT}&longitude={LON}&hourly=pm10,carbon_monoxide,ozone"
)

BROKER_URL = "http://broker:5001/publish"
TOPIC = "air_quality"
# PUBLISHER_ID = "air_sensor_1"

def get_air_quality_data():
    try:
        response = requests.get(AIR_QUALITY_URL)
        response.raise_for_status()
        data = response.json()

        latest = {
            "timestamp": time.time(),
            "pm10": data["hourly"]["pm10"][0],
            "carbon_monoxide": data["hourly"]["carbon_monoxide"][0],
            "ozone": data["hourly"]["ozone"][0],
        }
        return latest
    except requests.RequestException as e:
        print(f"❌ Error fetching air quality data: {e}")
        return None

def publish_air_quality():
    air_data = get_air_quality_data()
    if air_data:
        # Define severity condition (can be adjusted based on thresholds)
        pm10 = air_data["pm10"]
        co = air_data["carbon_monoxide"]
        ozone = air_data["ozone"]

        severe = pm10 > 80 or co > 5 or ozone > 180
        priority = 0 if severe else 2

        message = {
            "topic": TOPIC,
            "data": air_data,
            "priority": priority,
            # "publisher_id": PUBLISHER_ID
        }

        try:
            response = requests.post(BROKER_URL, json=message)
            response.raise_for_status()
            print("🌫️ Published air quality data:", message)
        except Exception as e:
            print("❌ Failed to publish air data:", e)
    else:
        print("⚠️ Skipping publish due to fetch error.")

if __name__ == "__main__":
    while True:
        publish_air_quality()
        time.sleep(20)  # Adjust frequency as needed
