FROM python:3.12-slim

WORKDIR /app

COPY subscribers/environmental_monitor .
COPY utils ./utils

RUN pip install flask requests

# Expose default port (can override in docker-compose)
EXPOSE 5000

# Replace the .py file with the actual one per component using docker-compose `command`
CMD ["python", "environmental_monitor.py"]
