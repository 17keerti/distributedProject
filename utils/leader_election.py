import requests
import threading
import time

class LeaderElection:
    def __init__(self, broker_id, known_peers_with_ids, announce_leader_callback=None):
        """
        Initialize LeaderElection with broker ID and known peers.
        
        Args:
            broker_id (int): The ID of the current broker.
            known_peers_with_ids (dict): Map of peer URL -> broker ID.
            announce_leader_callback (function): Optional callback when a new leader is elected.
        """
        self.broker_id = broker_id
        self.known_peers = known_peers_with_ids
        self.current_leader = None
        self.election_ongoing = False
        self.announce_leader_callback = announce_leader_callback
        self.lock = threading.Lock()  # To protect shared state

    def send_election_message(self, peer_url, peer_id, result_list):
        """
        Sends an election message to a peer broker with a higher ID.
        
        If the peer responds with "OK", it indicates it's alive and willing to participate.
        """
        try:
            print(f"📤 Sending election message to {peer_url} (broker {peer_id})", flush=True)
            res = requests.post(f"http://{peer_url}/election", json={"broker_id": self.broker_id}, timeout=2)
            if res.status_code == 200 and res.json().get("response") == "OK":
                print(f"👍 Received OK from broker {peer_id} at {peer_url}", flush=True)
                result_list.append(True)
        except Exception as e:
            print(f"❌ Election message to {peer_url} failed: {e}", flush=True)

    def announce_leader(self):
        """
        Announces the current broker as the leader to all known peers.
        """
        with self.lock:
            self.current_leader = self.broker_id
            self.election_ongoing = False

        print(f"🚨 Announcing self as leader {self.current_leader}", flush=True)

        # Notify all peers about new leader
        for peer_url in self.known_peers:
            try:
                requests.post(f"http://{peer_url}/leader", json={"leader_id": self.current_leader}, timeout=2)
                print(f"📢 Announced leader to {peer_url}", flush=True)
            except Exception as e:
                print(f"⚠️ Leader announcement to {peer_url} failed: {e}", flush=True)

        # Trigger callback if any
        if self.announce_leader_callback:
            self.announce_leader_callback(self.current_leader)

    def start_election(self):
        """
        Starts a leader election by contacting brokers with higher IDs.
        """
        with self.lock:
            if self.election_ongoing:
                print("⚠️ Election already in progress", flush=True)
                return
            self.election_ongoing = True

        print(f"🎯 Broker {self.broker_id} starting election", flush=True)

        # Identify brokers with higher IDs than self
        higher_id_peers = {
            peer_url: peer_id for peer_url, peer_id in self.known_peers.items()
            if peer_id > self.broker_id
        }

        print(f"📡 Known peers: {self.known_peers}", flush=True)
        print(f"🔼 Higher ID peers: {higher_id_peers}", flush=True)

        responses = []
        threads = []

        # Send election messages concurrently
        for peer_url, peer_id in higher_id_peers.items():
            t = threading.Thread(target=self.send_election_message, args=(peer_url, peer_id, responses))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=3)

        # If no higher broker responds, become leader
        if not responses:
            self.announce_leader()
        else:
            print("⏳ Waiting for leader announcement", flush=True)
            wait_time = 5  # seconds
            start = time.time()
            # Wait a while to see if someone else announces as leader
            while time.time() - start < wait_time:
                with self.lock:
                    if self.current_leader and self.current_leader != self.broker_id:
                        self.election_ongoing = False
                        print(f"👑 Leader announcement received for broker {self.current_leader}", flush=True)
                        return
                time.sleep(0.5)

            # No announcement received → assume leadership
            print("⏳ Timeout waiting for leader announcement, announcing self", flush=True)
            self.announce_leader()

    def update_leader(self, leader_id):
        """
        Called when this broker receives a leader announcement from another broker.
        """
        with self.lock:
            self.current_leader = leader_id
            self.election_ongoing = False
        print(f"👑 Leader updated to broker {leader_id}", flush=True)

        # Notify local broker of new leader (if callback provided)
        if self.announce_leader_callback:
            self.announce_leader_callback(leader_id)

    def get_leader(self):
        """
        Returns the currently known leader.
        """
        with self.lock:
            return self.current_leader

    def start_health_monitor(self, current_leader_getter):
        """
        Starts a background thread to monitor the health of the current leader.

        If the leader is unreachable, it initiates a new election.
        """
        def monitor():
            while True:
                time.sleep(5)
                leader_id = current_leader_getter()

                # If no leader or self is leader, skip
                if leader_id is None or leader_id == self.broker_id:
                    continue

                # Check the current leader's health
                for peer_url, peer_id in list(self.known_peers.items()):
                    if peer_id == leader_id:
                        try:
                            res = requests.get(f"http://{peer_url}/ping", timeout=2)
                            if res.status_code != 200:
                                raise Exception("Bad response")
                        except Exception as e:
                            print(f"💥 Leader {leader_id} not responding: {e}. Initiating election.", flush=True)
                            self.start_election()

        # Start the monitor thread as a daemon
        threading.Thread(target=monitor, daemon=True).start()

    def reset(self):
        """
        Resets internal leader election state.
        """
        with self.lock:
            self.current_leader = None
            self.election_ongoing = False
        print("🔄 LeaderElection state reset", flush=True)

