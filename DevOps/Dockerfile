FROM ubuntu:22.04

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    docker-compose \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY webhook_server.py .
COPY ci_script.sh .
COPY notifier.py .
COPY .env .
COPY test_notification.py .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Make script executable
RUN chmod +x ci_script.sh

CMD ["python3", "webhook_server.py"]

