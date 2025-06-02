import threading
import time
import requests

def receive_gossip(request, sse_subscribers, sse_unsubscribed):
    incoming_sse = request.json.get("sse_subscribers", {})
    incoming_unsubs = request.json.get("unsubscribed", {})

    print(f"🤝 Received gossip update:", flush=True)
    for topic, clients in incoming_sse.items():
        if clients:
            print(f"   📡 SSE subscribers for {topic}: {clients}", flush=True)
        sse_subscribers[topic].update(clients)
        sse_unsubscribed[topic].difference_update(clients)

    for topic, removed in incoming_unsubs.items():
        if removed:
            print(f"   ❌ SSE unsubscriptions for {topic}: {removed}", flush=True)
        sse_unsubscribed[topic].update(removed)
        sse_subscribers[topic].difference_update(removed)

    return "OK", 200


def start_gossip_thread(sse_subscribers, sse_unsubscribed, known_peers):
    def gossip_loop():
        print("🧵 Gossip thread started...", flush=True)
        while True:
            time.sleep(10)
            if not known_peers:
                continue

            payload = {
                "sse_subscribers": {
                    topic: list(addrs - sse_unsubscribed[topic])
                    for topic, addrs in sse_subscribers.items()
                },
                "unsubscribed": {
                    topic: list(sse_unsubscribed[topic])
                    for topic in sse_unsubscribed
                    if sse_unsubscribed[topic]
                }
            }
            for peer in list(known_peers.keys()):
                try:
                    print(f"🔄 Preparing to send gossip to {peer}:")
                    for topic, clients in payload["sse_subscribers"].items():
                        print(f"    📡 {topic}: {clients}")
                    for topic, removed in payload["unsubscribed"].items():
                        print(f"    ❌ {topic}: {removed}")
                    if not payload["sse_subscribers"] and not payload["unsubscribed"]:
                        print("    ⛔ Nothing to gossip.")

                    res = requests.post(f"http://{peer}/gossip", json=payload, timeout=3)
                    print(f"📣 Sent gossip to {peer} – status: {res.status_code}", flush=True)
                
                except Exception as e:
                    print(f"⚠️ Gossip to {peer} failed: {e}", flush=True)
                    known_peers.pop(peer, None)

        sse_unsubscribed.clear()

    threading.Thread(target=gossip_loop, daemon=True).start()