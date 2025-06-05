FROM python:3.12-slim

WORKDIR /app

COPY subscribers/public_interface .
COPY utils ./utils

RUN pip install flask requests

EXPOSE 5000

CMD ["python", "public_interface.py"]
