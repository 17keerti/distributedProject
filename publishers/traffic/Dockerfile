FROM python:3.12-slim

WORKDIR /app

COPY publishers/traffic/traffic_publisher.py .
COPY utils ./utils

RUN pip install flask requests


# Replace the .py file with the actual one per component using docker-compose `command`
CMD ["python", "traffic_publisher.py"]
