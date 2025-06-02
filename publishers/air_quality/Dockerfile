FROM python:3.12-slim

WORKDIR /app

COPY publishers/air_quality/air_quality_publisher.py .
COPY utils ./utils

RUN pip install flask requests


# Replace the .py file with the actual one per component using docker-compose `command`
CMD ["python", "air_quality_publisher.py"]
