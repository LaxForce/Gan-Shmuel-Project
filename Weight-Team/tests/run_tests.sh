#!/bin/bash

echo "Running weight service tests..."

# Wait for service to be up
sleep 5

# Test health endpoint
if ! curl -sf "http://localhost:8081/health"; then
    echo "Health check failed!"
    exit 1
fi

# Test weight API endpoint
if ! curl -sf "http://localhost:8081/api/weight"; then
    echo "Weight API test failed!"
    exit 1
fi

echo "All weight tests passed!"
exit 0
