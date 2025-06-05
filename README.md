# Distributed Project

## Project Setup and Compilation Guide

This project is a distributed system designed to simulate a smart city data stream, utilizing a publish-subscribe model with a leader election mechanism, gossip protocol for state synchronization, and Server-Sent Events (SSE) for real-time updates to clients. The system is orchestrated using Docker Compose.

### 1. Project Structure

The project consists of the following main components:

* **Broker**: Handles message routing, topic subscriptions, leader election, and gossip communication among brokers.
* **Publishers**: Simulate data sources (e.g., air quality, traffic, weather) and publish data to the broker.
* **Subscribers**: Consume data from the broker (e.g., environmental monitor, public interface, traffic manager).
* **Frontend**: A web interface for users to subscribe and view real-time data streams.
* **Utils**: Contains helper modules for Lamport clock, leader election, and gossip protocol.

### 2. Prerequisites

Before setting up and running the project, ensure you have the following installed on your system:

* **Docker**: For containerization of services.
* **Docker Compose**: For defining and running multi-container Docker applications.

### 3. Step-by-Step Setup and Execution

Follow these steps to get the `distributedProject` up and running:

1.  **Navigate to the Project Root:**
    Open your terminal or command prompt and navigate to the root directory of the `distributedProject`. This directory should contain the `docker-compose.yaml` file.

    ```bash
    cd distributedProject/
    ```

2.  **Build and Run Docker Containers:**
    The `docker-compose.yaml` file defines all the services (brokers, publishers, subscribers, frontend) and their configurations. Use Docker Compose to build the necessary Docker images and start all the services:

    ```bash
    docker-compose up --build
    ```

    * `docker-compose up`: Starts the services defined in `docker-compose.yaml`.
    * `--build`: This flag ensures that Docker images are built from their respective Dockerfiles (e.g., `broker/Dockerfile`, `publishers/air_quality/Dockerfile`, etc.) before starting the containers. This is crucial for the initial setup or after any code changes.

    This command will:
    * Build Docker images for `broker`, `air_quality_publisher`, `traffic_publisher`, `weather_publisher`, `environmental_monitor`, `traffic_manager`, `public_interface`, and `frontend`.
    * Start three `broker` instances (`broker`, `broker2`, `broker3`) to demonstrate leader election.
    * Start the `air_quality_publisher`, `traffic_publisher`, and `weather_publisher` to generate data.
    * Start `environmental_monitor`, `traffic_manager`, and `public_interface` as subscribers.
    * Start the `frontend` service.

    You will see logs from all services in your terminal.

3.  **Access the Frontend (Web Interface):**
    Once all services are up and running, you can access the frontend web interface through your web browser. The `docker-compose.yaml` exposes the frontend on port `6001`.

    Open your web browser and navigate to:

    ```
    http://localhost:6001
    ```

    You should see the "Smart City Data Stream" interface. From this interface, you can select a topic (Air Quality, Traffic, Weather) and subscribe to receive real-time data updates.

4.  **Observe Data Streams:**
    * On the frontend, select a topic (e.g., "Traffic") from the dropdown and click "Subscribe". You will start seeing incoming messages related to that topic in the "Live Stream" log.
    * You can open multiple browser tabs or windows and subscribe to different topics or the same topic to see how the SSE updates work.

5.  **Stop the Services:**
    To stop all running Docker containers and remove the networks created by Docker Compose, press `Ctrl+C` in your terminal where `docker-compose up` is running. Then, execute the following command:

    ```bash
    docker-compose down
    ```

    This will gracefully shut down and remove the containers, networks, and volumes created by `docker-compose up`.

### 4. Dependencies

The Python services in this project rely on external libraries. These dependencies are listed in `requirements.txt` files within the respective service directories.
* `flask`
* `requests`
* `sseclient`

### 5. Divison of Work

| Task | Team Member |
| :------------------------------------ | :--------------- |
| Research and Proposal | Keerti and Meghana |
| Brokers, Subscribers and Publishers | Keerti |
| Frontend | Keerti and Meghana |
| Google cloud Deployment | Keerti |
| Utilities (Algorithms implementations) | Keerti |
| Presentation and Video Recording | Keerti and Meghana |
| Report | Keerti and Meghana |
