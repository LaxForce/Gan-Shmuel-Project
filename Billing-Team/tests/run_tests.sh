#!/bin/bash

# Hardcode environment variables
export SERVICE_HOST="ci_test_billing"
export WEIGHT_HOST="ci_test_weight"
export SERVICE_PORT="8082"
export WEIGHT_PORT="8081"


echo "Running billing service tests..."

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

