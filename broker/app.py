from flask import Flask, request, jsonify, Response, stream_with_context
import requests
from collections import defaultdict, deque
import threading
import time
import random
import os
import queue
from utils.leader_election import LeaderElection

app = Flask(__name__)

# --- Broker Configuration ---
BROKER_ID = int(os.environ.get("BROKER_ID", "1"))
CURRENT_LEADER = None

# --- State Management ---
subscriptions = defaultdict(list)
unsubscribed = defaultdict(set)
sse_clients = defaultdict(list)                      # Active SSE queues per topic
sse_subscribers = defaultdict(set)                  # Subscribed client IPs per topic
sse_unsubscribed = defaultdict(set)                 # Recently unsubscribed clients per topic
message_queues = defaultdict(lambda: {"high": deque(), "low": deque()})
logs = defaultdict(list)                            # Topic-wise message logs

# --- Peer Awareness ---
def get_known_peers(my_id):
    all_peers = {
        1: "broker:5001",
        2: "broker2:5001",
        3: "broker3:5001"
    }
    return {url: id for id, url in all_peers.items() if id != my_id}

known_peers = get_known_peers(BROKER_ID)

# --- Leader Election Handler ---
def on_leader_update(new_leader):
    global CURRENT_LEADER
    CURRENT_LEADER = new_leader
    print(f"👑 Leader updated to broker {new_leader}", flush=True)

leader_election = LeaderElection(BROKER_ID, known_peers, on_leader_update)


# --- SSE Streaming Endpoint ---
@app.route('/stream/<topic>')
def stream(topic):
    def event_stream():
        q = queue.Queue()
        sse_clients[topic].append(q)
        client_ip = request.remote_addr
        print(f"🔔 SSE client connected to topic: {topic} from {client_ip}", flush=True)

        # Update subscriber state
        sse_subscribers[topic].add(client_ip)
        sse_unsubscribed[topic].discard(client_ip)

        try:
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            sse_clients[topic].remove(q)
            sse_subscribers[topic].discard(client_ip)  # 🔧 This line is crucial
            sse_unsubscribed[topic].add(client_ip)
            print(f"🔕 SSE client disconnected from topic: {topic}", flush=True)

    return Response(stream_with_context(event_stream()), content_type='text/event-stream')


# --- SSE Subscribe Endpoint ---
@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json(force=True)
    topic = data.get("topic")
    mode = data.get("mode")

    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    if mode == "sse":
        print(f"✅ SSE subscription requested for topic '{topic}'", flush=True)
        sse_subscribers[topic].add(request.remote_addr)
        sse_unsubscribed[topic].discard(request.remote_addr)
        return jsonify({"message": f"Subscribed to topic '{topic}' via SSE"}), 200

    elif mode == "webhook" or not mode:
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing URL for webhook subscription"}), 400
        if url not in subscriptions[topic]:
            subscriptions[topic].append(url)
            unsubscribed[topic].discard(url)
            print(f"✅ Webhook subscriber subscribed to '{topic}' at {url}", flush=True)
        return jsonify({"message": f"Subscribed to topic '{topic}' (webhook)"}), 200

    return jsonify({"error": f"Unsupported subscription mode: {mode}"}), 400


# --- SSE Unsubscribe Endpoint ---
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    data = request.get_json(force=True)
    topic = data.get("topic")
    mode = data.get("mode")

    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    if mode == "sse":
        print(f"🔕 SSE unsubscription requested for topic '{topic}'", flush=True)
        sse_subscribers[topic].discard(request.remote_addr)
        sse_unsubscribed[topic].add(request.remote_addr)
        return jsonify({"message": f"Unsubscribed from topic '{topic}' (SSE)"}), 200

    elif mode == "webhook" or not mode:
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing URL for webhook unsubscription"}), 400
        if topic in subscriptions and url in subscriptions[topic]:
            subscriptions[topic].remove(url)
            unsubscribed[topic].add(url)
            print(f"🛑 Unsubscribed: {url} from '{topic}' (webhook)")
            return jsonify({"message": f"Unsubscribed from topic '{topic}' (webhook)"}), 200
        return jsonify({"message": f"Not subscribed to '{topic}' with URL '{url}'"}), 200

    return jsonify({"error": f"Unsupported unsubscription mode: {mode}"}), 400


# --- Publish Messages ---
@app.route('/publish', methods=['POST'])
def publish():
    data = request.get_json(force=True)
    topic = data.get("topic")
    raw_priority = str(data.get("priority", "low")).lower()
    priority = "high" if raw_priority in ["0", "high"] else "low"

    if not topic:
        return jsonify({"error": "No topic specified"}), 400

    # Forward to leader if not self
    if CURRENT_LEADER and CURRENT_LEADER != BROKER_ID:
        leader_url = {
            1: "http://broker:5001",
            2: "http://broker2:5001",
            3: "http://broker3:5001"
        }.get(CURRENT_LEADER)
        if leader_url:
            try:
                res = requests.post(f"{leader_url}/publish", json=data, timeout=2)
                return res.content, res.status_code, res.headers.items()
            except Exception as e:
                return jsonify({"error": f"Failed to contact leader: {str(e)}"}), 500
        else:
            return jsonify({"error": "Unknown leader ID"}), 500

    # Enqueue message locally
    message_queues[topic][priority].append(data)
    logs[topic].append(data)
    if len(logs[topic]) > 1000:
        logs[topic] = logs[topic][-1000:]

    print(f"\n📬 Received message for topic '{topic}' with priority '{priority}'")
    print(f"Queue state: {[(p, len(q)) for p, q in message_queues[topic].items()]}", flush=True)

    # Dispatch to SSE clients
    for priority_level in ["high", "low"]:
        while message_queues[topic][priority_level]:
            message = message_queues[topic][priority_level].popleft()
            for q in sse_clients[topic]:
                try:
                    q.put(jsonify(message).get_data(as_text=True))
                except Exception as e:
                    print(f"❌ Failed to send SSE to client: {e}", flush=True)

    return '', 200


# --- Gossip Receive Endpoint ---
@app.route('/gossip', methods=['POST'])
def receive_gossip():
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


# --- Gossip Loop ---
def gossip_loop():
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


# --- Leader Election Endpoints ---
@app.route('/election', methods=['POST'])
def election():
    data = request.get_json(force=True)
    sender_id = int(data.get("broker_id"))
    print(f"⚡ Received election from broker {sender_id}", flush=True)
    if BROKER_ID > sender_id:
        return jsonify({"response": "OK"}), 200
    return jsonify({"response": "NO"}), 200


@app.route('/leader', methods=['POST'])
def leader_announcement():
    data = request.get_json(force=True)
    leader_id = int(data.get("leader_id"))
    leader_election.update_leader(leader_id)
    return '', 200


@app.route('/get_leader', methods=['GET'])
def get_leader():
    print(f"📥 Received /get_leader request. Returning {leader_election.get_leader()}", flush=True)
    return jsonify({"leader_id": leader_election.get_leader()}), 200


@app.route('/start_election', methods=['POST'])
def start_election():
    election.start_election()
    return jsonify({"status": "started"}), 200

# --- Debug / Health ---
@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/logs/<topic>', methods=['GET'])
def view_logs(topic):
    return jsonify({"topic": topic, "logs": logs.get(topic, [])}), 200


# --- Main Startup ---
if __name__ == '__main__':
    print(f"🚀 Broker {BROKER_ID} running on port 5001...", flush=True)
    threading.Thread(target=gossip_loop, daemon=True).start()

    def delayed_election():
        time.sleep(5)
        leader_election.start_election()

    threading.Thread(target=delayed_election, daemon=True).start()
    app.run(host='0.0.0.0', port=5001)
