FROM ubuntu:24.04

# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose \
    git \
    curl \
    htop \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd for web terminal
RUN curl -L https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Install LazyDocker
RUN curl -L https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash \
&& mv /root/.local/bin/lazydocker /usr/local/bin/lazydocker \
&& chmod +x /usr/local/bin/lazydocker 
# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies in the virtual environment
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

# Add monitoring module files
COPY monitoring/ /app/monitoring/

CMD ["python3", "webhook_server.py"]

