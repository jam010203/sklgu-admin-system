# Dockerfile for Fly.io deployment
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=admin_system/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Use Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:5000", "admin_system.app:app"]
