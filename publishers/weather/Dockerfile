FROM python:3.10-slim

WORKDIR /app

COPY publishers/weather/weather_publisher.py .
COPY utils ./utils

RUN pip install requests

CMD ["python", "weather_publisher.py"]
