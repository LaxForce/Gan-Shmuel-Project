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
    
    cd /app && python3 << EOF
import os
import sys
sys.path.append(os.getcwd())  # Add current directory (/app) to Python path
from notifier import CINotifier
import logging

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
    local service=$1      # Service name (e.g., 'weight', 'billing')
    local port=$2        # Port to check health on
    local environment=$3  # Added parameter for environment
    local retries=5
    local delay=10

    # Construct hostname dynamically based on environment
    local hostname
    if [ "$environment" = "prod" ]; then
        hostname="ci_prod_${service}"
    else
        hostname="ci_test_${service}"
    fi

    log "Checking health of ${service} service at http://${hostname}:${port}/health..."
    
    for ((i=1; i<=retries; i++)); do
        if curl -sf "http://${hostname}:${port}/health" > /dev/null; then
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
        port=8081  # TODO: move to config, read from file
    elif [ "$service" = "billing" ]; then
        port=8082  # TODO: move to config, read from file
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
    if [ -f "Weight-Team/docker-compose.${environment}.yml" ]; then
        docker-compose -f "Weight-Team/docker-compose.${environment}.yml" down --volumes --remove-orphans || true
    fi
    
    # Clean up billing service
    if [ -f "Billing-Team/docker-compose.${environment}.yml" ]; then
        docker-compose -f "Billing-Team/docker-compose.${environment}.yml" down --volumes --remove-orphans || true
    fi
    
    # # Remove any leftover test containers with our project prefix
    docker ps -a | grep "ci_test_" | awk '{print $1}' | xargs -r docker rm -f || true
    # # Remove any leftover test networks with our project prefix

    # docker network ls | grep "ci_test_" | awk '{print $1}' | xargs -r docker network rm || true
    
    # Clean up repository if it exists
    if [ -d "repo" ]; then
        rm -rf repo
    fi

    # TODO: Add any other cleanup steps as needed (e.g. logs, event jsons, etc.)
}

# Function to deploy a service
deploy_service() {
    local service=$1      # Will be 'weight' or 'billing'
    local environment=$2  # Will be 'test' or 'prod'
    local compose_file="docker-compose.${environment}.yml"
   
    # First go back to repo root
    cd /app/repo
    
    # Debug info
    #log "DEBUG: Deploying service ${service} in ${environment} environment"
    #log "DEBUG: Current directory: $(pwd)"
    
    if [ "$environment" = "test" ]; then
        log "Creating test network..."
        docker network create ci_test_network 2>/dev/null || true
        # if ! docker network create --driver bridge --opt "com.docker.network.bridge.name"="ci_test_network" ci_test_network 2>/dev/null; then
        #     log "Test network already exists or failed to create"
        # fi
    else
        log "Creating production network..."
        docker network create ci_prod_network 2>/dev/null || true
        # if ! docker network create --driver bridge --opt "com.docker.network.bridge.name"="ci_prod_network" ci_prod_network 2>/dev/null; then
        #     log "Production network already exists or failed to create"
        # fi    
    fi
    
    # Map service names to directory names
    local service_dir
    case "$service" in
        "weight")
            service_dir="Weight-Team"
            ;;
        "billing")
            service_dir="Billing-Team"
            ;;
        *)
            log "Unknown service: ${service}"
            return 1
            ;;
    esac
    
    #log "DEBUG: Trying to cd to ${service_dir}"
    cd "${service_dir}"
    
    log "Deploying ${service} in ${environment} environment..."
    
    # Clean up ALL existing containers related to this service - DEBUG, can comment and uncomment as needed
    #log "DEBUG: Cleaning up any existing containers"
    docker rm -f "ci_test_${service}" "ci_prod_${service}" 2>/dev/null || true
    
    # Clean up images - DEBUG, can comment and uncomment as needed
    #log "DEBUG: Cleaning up any existing images" 
    docker rmi -f "${service_dir,,}_${service}" 2>/dev/null || true
    
    # Copy environment file (now using single .env)
    if [ -f "/app/.env" ]; then
        cp "/app/.env" .env
    else
        log "Warning: No .env file found"
    fi
    
    # Debug compose file -- uncomment when needed
    #log "DEBUG: Checking compose file content:"
    #cat "$compose_file"
    
    # Build and start the service
    #log "DEBUG: Running docker-compose with environment ${environment}"
    #if ! docker-compose -f "$compose_file" up -d --build --no-recreate; then
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
    if ! check_health "weight" 8081 "test"; then
        notify "FAILURE" "Weight service failed health check"
        return 1
    fi
    
    # Run weight service tests
    log "Running weight service tests..."
    cd Weight-Team
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
    if ! check_health "billing" 8082 "test"; then
        notify "FAILURE" "Billing service failed health check"
        return 1
    fi
    
    # Run billing service tests
    log "Running billing service tests..."
    cd Billing-Team
    if ! run_service_tests "billing"; then
        notify "FAILURE" "Billing service tests failed"
        cd ..
        return 1
    fi
    cd ..
    
    notify "SUCCESS" "All tests passed"
    cleanup
    return 0
}

# Function to handle production deployment
deploy_production() {
    #log "DEBUG: Starting production deployment function"
    log "Starting production deployment..."

    # Create production network if it doesn't exist
    if ! docker network create ci_prod_network; then
        notify "FAILURE" "Failed to create production network"
        return 1
    fi  
    
    # Deploy weight service first
    if ! deploy_service "weight" "prod"; then
        notify "FAILURE" "Failed to deploy weight service to production"
        return 1
    fi
    
    # Check weight service health
    if ! check_health "weight" 8081 "prod"; then
        notify "FAILURE" "Weight service unhealthy in production"
        return 1
    fi
    
    # Deploy billing service
    if ! deploy_service "billing" "prod"; then
        notify "FAILURE" "Failed to deploy billing service to production"
        return 1
    fi
    
    # Check billing service health
    if ! check_health "billing" 8082 "prod"; then
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
    
    trap 'cleanup "test"' EXIT

    # # Create network for testing
    # log "Creating test network..."
    # if ! docker network create ci_test_network 2>/dev/null; then
    #     notify "FAILURE" "Failed to create test network"
    #     exit 1
    # fi
    
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
    
        #log "DEBUG: Tests passed, checking branch condition"
        #log "DEBUG: Current branch is '${BRANCH}'"
    
        if [ "$BRANCH" = "master" ]; then
            #log "DEBUG: Branch match found, should proceed to production"
            log "Tests passed on master branch, proceeding with production deployment..."
            trap 'cleanup "test"' EXIT
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

# Run main function
main
