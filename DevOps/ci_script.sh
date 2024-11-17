#!/bin/bash
set -e  # Exit on any error

# Setup logging
LOG_FILE="/app/logs/ci_${TIMESTAMP}.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

# Helper function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Enhanced notification function
notify() {
    local status=$1
    local message=$2
    
    log "CI ${status}: ${message}"
    
    python3 << EOF
from notifier import CINotifier
import logging
import os
logging.basicConfig(level=logging.INFO)
notifier = CINotifier()
success = notifier.send_notification(
    "${status}",
    "${message}",
    "${LOG_FILE}"
)
if not success:
    print("Failed to send notification email!")
    exit(1)
EOF
}

# Function to check container health with retries
check_health() {
    local service=$1
    local port=$2
    local retries=5
    local delay=10
    
    log "Checking health of ${service} service..."
    
    for ((i=1; i<=retries; i++)); do
        if curl -sf "http://localhost:${port}/health" > /dev/null; then
            log "${service} is healthy"
            return 0
        fi
        log "Health check attempt ${i}/${retries} failed, waiting ${delay}s..."
        sleep $delay
    done
    
    log "${service} health check failed after ${retries} attempts"
    return 1
}

# Function to run service tests
run_service_tests() {
    local service=$1
    local test_script="./tests/run_tests.sh"
    
    # Set correct port based on service
    local port
    if [ "$service" = "weight" ]; then
        port=8081
    elif [ "$service" = "billing" ]; then
        port=8082
    else
        log "Unknown service: ${service}"
        return 1
    fi
    
    if [ -f "$test_script" ]; then
        log "Running ${service} tests using provided test script..."
        chmod +x "$test_script"
        if ! timeout 300 "$test_script"; then
            log "${service} tests failed"
            return 1
        fi
    else
        log "No test script found for ${service}, using basic health check..."
        if ! check_health "$service" "$port"; then
            log "${service} health check failed"
            return 1
        fi
    fi
    
    return 0
}

# Enhanced cleanup function
cleanup() {
    local environment=$1  # test or prod
    log "Cleaning up ${environment} environment..."
    
    # Clean up weight service
    if [ -f "weight/docker-compose.${environment}.yml" ]; then
        docker-compose -f "weight/docker-compose.${environment}.yml" down --volumes --remove-orphans || true
    fi
    
    # Clean up billing service
    if [ -f "billing/docker-compose.${environment}.yml" ]; then
        docker-compose -f "billing/docker-compose.${environment}.yml" down --volumes --remove-orphans || true
    fi
    
    # Remove any leftover containers with our project prefix
    docker ps -a | grep "ci_test_" | awk '{print $1}' | xargs -r docker rm -f || true
    
    # Clean up repository if it exists
    if [ -d "repo" ]; then
        rm -rf repo
    fi
}

# Function to deploy a service
deploy_service() {
    local service=$1
    local environment=$2
    local compose_file="docker-compose.${environment}.yml"
    
    log "Deploying ${service} in ${environment} environment..."
    
    cd "${service}"
    
    # Copy environment file (now using single .env)
    if [ -f "/app/.env" ]; then
        cp "/app/.env" .env
    else
        log "Warning: No .env file found"
    fi
    
    # Build and start the service
    if ! timeout 300 docker-compose -f "$compose_file" up -d --build; then
        log "Failed to deploy ${service}"
        cd ..
        return 1
    fi
    
    cd ..
    return 0
}

# Function to run test environment
run_tests() {
    log "Setting up test environment..."
    
    # First deploy weight service (as billing depends on it)
    log "Deploying weight service..."
    if ! deploy_service "weight" "test"; then
        notify "FAILURE" "Failed to deploy weight service"
        return 1
    fi
    
    # Wait for weight service to be healthy
    if ! check_health "weight" 8081; then
        notify "FAILURE" "Weight service failed health check"
        return 1
    fi
    
    # Run weight service tests
    log "Running weight service tests..."
    cd weight
    if ! run_service_tests "weight"; then
        notify "FAILURE" "Weight service tests failed"
        cd ..
        return 1
    fi
    cd ..
    
    # Now deploy billing service
    log "Deploying billing service..."
    if ! deploy_service "billing" "test"; then
        notify "FAILURE" "Failed to deploy billing service"
        return 1
    fi
    
    # Wait for billing service to be healthy
    if ! check_health "billing" 8082; then
        notify "FAILURE" "Billing service failed health check"
        return 1
    fi
    
    # Run billing service tests
    log "Running billing service tests..."
    cd billing
    if ! run_service_tests "billing"; then
        notify "FAILURE" "Billing service tests failed"
        cd ..
        return 1
    fi
    cd ..
    
    notify "SUCCESS" "All tests passed"
    return 0
}

# Function to handle production deployment
deploy_production() {
    log "Starting production deployment..."
    
    # Deploy weight service first
    if ! deploy_service "weight" "prod"; then
        notify "FAILURE" "Failed to deploy weight service to production"
        return 1
    fi
    
    # Check weight service health
    if ! check_health "weight" 8081; then
        notify "FAILURE" "Weight service unhealthy in production"
        return 1
    fi
    
    # Deploy billing service
    if ! deploy_service "billing" "prod"; then
        notify "FAILURE" "Failed to deploy billing service to production"
        return 1
    fi
    
    # Check billing service health
    if ! check_health "billing" 8082; then
        notify "FAILURE" "Billing service unhealthy in production"
        return 1
    fi
    
    notify "SUCCESS" "Production deployment completed"
    return 0
}

# Main CI process
main() {
    log "Starting CI process for branch ${BRANCH}"
    log "Commit: ${COMMIT_SHA}"
    log "Repository: ${REPO_URL}"
    
    # Ensure clean start
    cleanup "test"
    cleanup "prod"
    
    # Clone repository
    log "Cloning repository..."
    if ! git clone "${REPO_URL}" repo; then
        notify "FAILURE" "Failed to clone repository"
        exit 1
    fi
    
    cd repo
    
    # Checkout specific commit
    log "Checking out commit ${COMMIT_SHA}..."
    git checkout "${COMMIT_SHA}"
    
    # Run tests and handle the result
    if run_tests; then
        if [ "$BRANCH" = "master" ]; then
            log "Tests passed on master branch, proceeding with production deployment..."
            if deploy_production; then
                notify "SUCCESS" "CI process completed successfully with production deployment"
            else
                notify "FAILURE" "Production deployment failed"
                exit 1
            fi
        else
            log "Tests passed on ${BRANCH} branch"
            notify "SUCCESS" "CI process completed successfully"
        fi
    else
        notify "FAILURE" "CI process failed during testing"
        exit 1
    fi
}

# Trap cleanup for both test and prod environments
trap 'cleanup "test"; cleanup "prod"' EXIT

# Run main function
main
