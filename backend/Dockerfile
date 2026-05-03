# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (mysqlclient requires gcc)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables for production
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Copy and set entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Seed DB + start Gunicorn (seeds are idempotent via ON DUPLICATE KEY)
ENTRYPOINT ["./entrypoint.sh"]
