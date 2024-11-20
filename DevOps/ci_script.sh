#!/bin/bash
set -e  # Exit on any error

# Port Configuration
WEIGHT_PROD_PORT=8081
BILLING_PROD_PORT=8082
WEIGHT_TEST_PORT=5000
BILLING_TEST_PORT=5001
WEIGHT_DB_PROD_PORT=3306
WEIGHT_DB_TEST_PORT=3307
BILLING_DB_PROD_PORT=3308
BILLING_DB_TEST_PORT=3309

# Setup logging
LOG_FILE="/app/logs/ci_${TIMESTAMP}.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

# Helper function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to get service port
get_service_port() {
    local service=$1
    local environment=$2
    
    case "$service" in
        "weight")
            if [ "$environment" = "prod" ]; then
                echo "$WEIGHT_PROD_PORT"
            else
                echo "$WEIGHT_TEST_PORT"
            fi
            ;;
        "billing")
            if [ "$environment" = "prod" ]; then
                echo "$BILLING_PROD_PORT"
            else
                echo "$BILLING_TEST_PORT"
            fi
            ;;
    esac
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
    local port=$(get_service_port "$service" "$3")
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
    
    # Get port based on service
    local port=$(get_service_port "$service" "test")
    
    if [ -f "$test_script" ]; then
        log "Running ${service} tests using provided test script..."
        chmod +x "$test_script"
        
        # Export port for test script to use
        export SERVICE_PORT=$port
        export WEIGHT_PORT=$WEIGHT_TEST_PORT  # For billing service to know where weight is
        
        if ! timeout 300 "$test_script"; then
            log "${service} tests failed"
            return 1
        fi
    else
        log "No test script found for ${service}, using basic health check..."
        if ! check_health "$service" "$port" "test"; then
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
    if [ -f "billing_team/docker-compose.${environment}.yml" ]; then
        docker-compose -f "billing_team/docker-compose.${environment}.yml" down --volumes --remove-orphans || true
    fi
    
    # Remove any leftover test containers with our project prefix
    docker ps -a | grep "ci_test_" | awk '{print $1}' | xargs -r docker rm -f || true
    
    # Clean up repository if it exists
    if [ -d "repo" ]; then
        rm -rf repo
    fi
}

# Function to deploy a service
deploy_service() {
    local service=$1      # Will be 'weight' or 'billing'
    local environment=$2  # Will be 'test' or 'prod'
    local compose_file="docker-compose.${environment}.yml"
   
    # First go back to repo root
    cd /app/repo
    
    if [ "$environment" = "test" ]; then
        log "Creating test network..."
        docker network create ci_test_network 2>/dev/null || true
    else
        log "Creating production network..."
        docker network create ci_prod_network 2>/dev/null || true
    fi
    
    # Map service names to directory names
    local service_dir
    case "$service" in
        "weight")
            service_dir="Weight-Team"
            ;;
        "billing")
            service_dir="billing_team"
            ;;
        *)
            log "Unknown service: ${service}"
            return 1
            ;;
    esac
    
    cd "${service_dir}"
    
    log "Deploying ${service} in ${environment} environment..."
    
    # Clean up existing containers
    docker rm -f "ci_test_${service}" "ci_prod_${service}" 2>/dev/null || true
    docker rmi -f "${service_dir,,}_${service}" 2>/dev/null || true
    
    # Copy environment file (now using single .env)
    if [ -f "/app/.env" ]; then
        cp "/app/.env" .env
    else
        log "Warning: No .env file found"
    fi
    
    # Export port for docker-compose
    export SERVICE_PORT=$(get_service_port "$service" "$environment")
    if [ "$service" = "billing" ]; then
        export WEIGHT_PORT=$(get_service_port "weight" "$environment")
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
    if ! check_health "weight" "$WEIGHT_TEST_PORT" "test"; then
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
    if ! check_health "billing" "$BILLING_TEST_PORT" "test"; then
        notify "FAILURE" "Billing service failed health check"
        return 1
    fi
    
    # Run billing service tests
    log "Running billing service tests..."
    cd billing_team
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

    # Create production network if it doesn't exist
    if ! docker network create ci_prod_network 2>/dev/null; then
        log "Production network already exists or failed to create"
    fi
    
    # Deploy weight service first
    if ! deploy_service "weight" "prod"; then
        notify "FAILURE" "Failed to deploy weight service to production"
        return 1
    fi
    
    # Check weight service health
    if ! check_health "weight" "$WEIGHT_PROD_PORT" "prod"; then
        notify "FAILURE" "Weight service unhealthy in production"
        return 1
    fi
    
    # Deploy billing service
    if ! deploy_service "billing" "prod"; then
        notify "FAILURE" "Failed to deploy billing service to production"
        return 1
    fi
    
    # Check billing service health
    if ! check_health "billing" "$BILLING_PROD_PORT" "prod"; then
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

# Run main function
main
