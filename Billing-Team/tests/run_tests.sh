#!/bin/bash

echo "Running billing service tests..."

# Wait for service to be up
sleep 5

# Test health endpoint
if ! curl -sf "http://localhost:8082/health"; then
    echo "Health check failed!"
    exit 1
fi

# Test billing API endpoint
if ! curl -sf "http://localhost:8082/api/billing"; then
    echo "Billing API test failed!"
    exit 1
fi

# Test dependency on weight service
if ! curl -sf "http://localhost:8081/api/weight"; then
    echo "Weight service dependency test failed!"
    exit 1
fi

echo "All billing tests passed!"
exit 0
