FROM python:3.12-slim

WORKDIR /app

COPY subscribers/environmental_monitor .
COPY utils ./utils

RUN pip install flask requests

EXPOSE 5000

CMD ["python", "environmental_monitor.py"]
