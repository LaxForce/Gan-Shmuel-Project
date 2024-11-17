#!/bin/bash

echo "Running weight service tests..."

# Detect environment and set SERVICE_HOST
if [ -z "$SERVICE_HOST" ]; then
    if [ -n "$(grep docker /proc/1/cgroup)" ]; then
        # Running inside Docker, use the default Docker service name
        SERVICE_HOST="ci_test_weight"
    else
        # Running locally, default to localhost
        SERVICE_HOST="localhost"
    fi
fi

# Default port
SERVICE_PORT="${SERVICE_PORT:-8081}"

# Wait for service to be up
sleep 5

# Test health endpoint
if ! curl -sf "http://${SERVICE_HOST}:${SERVICE_PORT}/health"; then
    echo "Health check failed!"
    exit 1
fi

# Test weight API endpoint
if ! curl -sf "http://${SERVICE_HOST}:${SERVICE_PORT}/api/weight"; then
    echo "Weight API test failed!"
    exit 1
fi

echo "All weight tests passed!"
exit 0

