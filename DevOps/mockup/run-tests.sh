#!/bin/bash
set -e

# Wait for container to be healthy
sleep 5

# Check if container is running
if docker ps | grep -q "mockup_test"; then
    echo "Mockup test container is healthy"
    exit 0
else
    echo "Mockup test container is not healthy"
    exit 1
fi
