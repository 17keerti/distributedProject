FROM python:3.12-slim

WORKDIR /app

COPY subscribers/traffic_manager .
COPY utils ./utils

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "traffic_manager.py"]
