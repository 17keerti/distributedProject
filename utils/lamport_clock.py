
class LamportClock:
    def __init__(self):
        self.time = 0

    def tick(self):
        """Increment clock on internal event."""
        self.time += 1
        return self.time

    def receive(self, other_time):
        """Adjust clock on receiving a message."""
        self.time = max(self.time, other_time) + 1
        return self.time

    def get_time(self):
        return self.time
