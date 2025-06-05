class LamportClock:
    def __init__(self):
        # Initialize the Lamport clock to 0
        self.time = 0

    def tick(self):
        """
        Called when a local/internal event occurs.
        Increments the logical clock by 1.
        
        Returns:
            int: The updated clock value.
        """
        self.time += 1
        return self.time

    def receive(self, other_time):
        """
        Called when a message is received from another process.
        Updates the local clock based on the sender's timestamp.

        Lamport rule: time = max(local, received) + 1

        Args:
            other_time (int): Timestamp from the sender.

        Returns:
            int: The updated clock value.
        """
        self.time = max(self.time, other_time) + 1
        return self.time

    def get_time(self):
        """
        Returns the current Lamport clock time.

        Returns:
            int: Current clock value.
        """
        return self.time
