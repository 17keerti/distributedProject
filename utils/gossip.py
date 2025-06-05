import threading
import time
import requests

def receive_gossip(request, sse_subscribers, sse_unsubscribed):
    """
    Receives gossip data from peer brokers to update local subscription state.

    Args:
        request: Flask request object with JSON containing gossip info.
        sse_subscribers (defaultdict(set)): Local map of topic -> active subscribers.
        sse_unsubscribed (defaultdict(set)): Local map of topic -> unsubscribed clients.

    Behavior:
        - Adds new subscribers received from other brokers.
        - Removes clients that have unsubscribed elsewhere.
    """
    # Extract incoming gossip state from JSON
    incoming_sse = request.json.get("sse_subscribers", {})
    incoming_unsubs = request.json.get("unsubscribed", {})

    print(f"🤝 Received gossip update:", flush=True)

    # Update local state with new subscriber data
    for topic, clients in incoming_sse.items():
        if clients:
            print(f"   📡 SSE subscribers for {topic}: {clients}", flush=True)
        sse_subscribers[topic].update(clients)  # Add new subscribers
        sse_unsubscribed[topic].difference_update(clients)  # Remove from unsubscribed set

    # Update unsubscribed set and remove those from active subscribers
    for topic, removed in incoming_unsubs.items():
        if removed:
            print(f"   ❌ SSE unsubscriptions for {topic}: {removed}", flush=True)
        sse_unsubscribed[topic].update(removed)  # Add to unsubscribed
        sse_subscribers[topic].difference_update(removed)  # Remove from active subscribers

    return "OK", 200


def start_gossip_thread(sse_subscribers, sse_unsubscribed, known_peers):
    """
    Starts a background thread that periodically sends gossip messages to all known peers.

    Args:
        sse_subscribers (defaultdict(set)): Local topic -> subscribers map.
        sse_unsubscribed (defaultdict(set)): Local topic -> unsubscribed clients map.
        known_peers (dict): Broker URL map to other peer brokers.
    """
    def gossip_loop():
        print("🧵 Gossip thread started...", flush=True)
        while True:
            time.sleep(10)  # Wait 10 seconds between gossip rounds

            if not known_peers:
                continue  # Skip if there are no known peers to gossip with

            # Construct payload for gossip message
            payload = {
                "sse_subscribers": {
                    topic: list(addrs - sse_unsubscribed[topic])  # Exclude unsubscribed addresses
                    for topic, addrs in sse_subscribers.items()
                },
                "unsubscribed": {
                    topic: list(sse_unsubscribed[topic])
                    for topic in sse_unsubscribed
                    if sse_unsubscribed[topic]  # Only include non-empty unsub lists
                }
            }

            # Send gossip update to each known peer
            for peer in list(known_peers.keys()):
                try:
                    print(f"🔄 Preparing to send gossip to {peer}:")

                    # Log current subscriber state being gossiped
                    for topic, clients in payload["sse_subscribers"].items():
                        print(f"    📡 {topic}: {clients}")
                    for topic, removed in payload["unsubscribed"].items():
                        print(f"    ❌ {topic}: {removed}")

                    if not payload["sse_subscribers"] and not payload["unsubscribed"]:
                        print("    ⛔ Nothing to gossip.")

                    # POST the gossip payload to peer's /gossip endpoint
                    res = requests.post(f"http://{peer}/gossip", json=payload, timeout=3)
                    print(f"📣 Sent gossip to {peer} – status: {res.status_code}", flush=True)

                except Exception as e:
                    # Log failure to contact peer
                    print(f"⚠️ Gossip to {peer} failed: {e}", flush=True)
                    # Optionally remove peer or retry later

            # ✅ After sending, clear unsubscribed records (they’ve been propagated)
            sse_unsubscribed.clear()

    # Start gossip thread as daemon so it doesn't block program exit
    threading.Thread(target=gossip_loop, daemon=True).start()
