#!/bin/bash

# Hardcode environment variables
export SERVICE_HOST="ci_test_weight"
export SERVICE_PORT="8081"

echo "Running weight service tests..."

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

