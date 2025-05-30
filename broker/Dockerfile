# Use official Python image
FROM python:3.12-slim

WORKDIR /app

# Copy the broker application files
COPY broker /app

# Copy the utils directory
COPY utils /app/utils

# Install dependencies
RUN pip install flask requests

# Expose default port (override in docker-compose)
EXPOSE 5000

# Default command (override in docker-compose)
CMD ["python", "app.py"]