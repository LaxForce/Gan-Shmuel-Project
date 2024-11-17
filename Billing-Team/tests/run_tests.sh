#!/bin/bash

echo "Running billing service tests..."

# Detect environment and set SERVICE_HOST and WEIGHT_HOST
if [ -z "$SERVICE_HOST" ]; then
    if [ -n "$(grep docker /proc/1/cgroup)" ]; then
        # Running inside Docker
        SERVICE_HOST="ci_test_billing"
        WEIGHT_HOST="ci_test_weight"
    else
        # Running locally
        SERVICE_HOST="localhost"
        WEIGHT_HOST="localhost"
    fi
fi

# Default ports
SERVICE_PORT="${SERVICE_PORT:-8082}"
WEIGHT_PORT="${WEIGHT_PORT:-8081}"

# Wait for service to be up
sleep 5

# Test health endpoint
if ! curl -sf "http://${SERVICE_HOST}:${SERVICE_PORT}/health"; then
    echo "Health check failed!"
    exit 1
fi

# Test billing API endpoint
if ! curl -sf "http://${SERVICE_HOST}:${SERVICE_PORT}/api/billing"; then
    echo "Billing API test failed!"
    exit 1
fi

# Test dependency on weight service
if ! curl -sf "http://${WEIGHT_HOST}:${WEIGHT_PORT}/api/weight"; then
    echo "Weight service dependency test failed!"
    exit 1
fi

echo "All billing tests passed!"
exit 0

