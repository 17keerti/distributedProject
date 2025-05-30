from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import requests
import time

app = Flask(__name__, template_folder='templates')

PORT = 6001
SERVICE_NAME = "frontend"

KNOWN_BROKERS = {
    1: "broker:5001",
    2: "broker2:5001",
    3: "broker3:5001",
}

def get_current_leader_url():
    for broker_id, broker_url in KNOWN_BROKERS.items():
        try:
            res = requests.get(f"http://{broker_url}/get_leader", timeout=2)
            if res.status_code == 200:
                leader_id = res.json().get("leader_id")
                return f"http://{KNOWN_BROKERS.get(leader_id)}"
        except:
            continue
    return None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json(force=True)
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Missing 'topic'"}), 400

    leader_url = get_current_leader_url()
    if not leader_url:
        return jsonify({"error": "Could not determine leader broker. Try again later."}), 503

    payload = {
        "topic": topic,
        "mode": "sse"
    }
    try:
        res = requests.post(f"{leader_url}/subscribe", json=payload, timeout=5)
        res.raise_for_status()
        return jsonify({"message": f"Subscribed to {topic}"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to subscribe: {str(e)}"}), 500

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    data = request.get_json(force=True)
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Missing 'topic'"}), 400

    leader_url = get_current_leader_url()
    if not leader_url:
        return jsonify({"error": "Could not determine leader broker. Try again later."}), 503

    payload = {
        "topic": topic,
        "mode": "sse"
    }
    try:
        res = requests.post(f"{leader_url}/unsubscribe", json=payload, timeout=5)
        res.raise_for_status()
        return jsonify({"message": f"Unsubscribed from {topic}"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to unsubscribe: {str(e)}"}), 500

@app.route('/stream')
def stream():
    topic = request.args.get("topic")
    if not topic:
        return "❌ Topic required in query params", 400

    leader_url = get_current_leader_url()
    if not leader_url:
        return "❌ Could not get current broker leader.", 503

    def proxy_sse():
        try:
            with requests.get(f"{leader_url}/stream/{topic}", stream=True) as r:
                for line in r.iter_lines(decode_unicode=True):
                    if line.startswith("data:"):
                        yield f"{line}\n\n"
        except Exception as e:
            yield f"data: {{\"error\": \"SSE proxy error: {str(e)}\"}}\n\n"

    return Response(stream_with_context(proxy_sse()), mimetype="text/event-stream")

if __name__ == '__main__':
    print(f"🚀 Subscriber frontend running at http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, threaded=True)