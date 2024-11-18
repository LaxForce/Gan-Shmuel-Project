#!/bin/bash
set -e  # Exit on any error

# Setup logging to both console and file
# ${TIMESTAMP} comes from the environment variables passed by webhook
LOG_FILE="/app/logs/ci_${TIMESTAMP}.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1  # Redirect stdout and stderr to both console and file

# Helper function for consistent log formatting
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Helper function for sending notifications
# Could be extended to send emails, Slack messages, etc.
notify() {
    local status=$1    # SUCCESS or FAILURE
    local message=$2   # Detailed message
    
    log "CI ${status}: ${message}"
    
    # Call Python notifier with proper environment variables and logging
    python3 << EOF
from notifier import CINotifier
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

# Call notifier with all necessary information
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

# Cleanup function to ensure test environment is removed
# even if tests fail
cleanup() {
    log "Cleaning up test environment..."
    # The '|| true' ensures the script doesn't exit if down fails
    docker-compose -f docker-compose.test.yml down || true
}

# Function to run all tests and health checks
run_tests() {
    log "Running tests..."

    # Start test environment using docker-compose
    log "Starting test environment..."
    docker-compose -f docker-compose.test.yml up -d

    # Give services time to start up
    log "Waiting for services to start..."
    sleep 30
    
    # Run health checks for each service
    local services=("weight" "billing" "devops")
    for service in "${services[@]}"; do
        log "Checking health of ${service} service..."
        if ! curl -f "http://${service}:8080/health"; then
            notify "FAILURE" "Health check failed for ${service}"
            cleanup
            return 1  # Return error status
        fi
    done
    
    # If we got here, all tests passed
    notify "SUCCESS" "All tests passed"
    return 0
}

# Function to handle production deployment
deploy_production() {
    log "Deploying to production..."
    docker-compose -f docker-compose.prod.yml up -d
    notify "SUCCESS" "Production deployment completed"
}

# Main CI process
main() {
    log "Starting CI process for branch ${BRANCH}"
    log "Commit: ${COMMIT_SHA}"
    log "Repository: ${REPO_URL}"

    # Clone the repository
    log "Cloning repository..."
    git clone ${REPO_URL} repo
    cd repo

    # Checkout specific commit
    log "Checking out commit ${COMMIT_SHA}..."
    git checkout ${COMMIT_SHA}

    # Run tests and handle the result
    if run_tests; then
        # If tests passed and we're on master branch, deploy to production
        if [ "$BRANCH" = "master" ]; then
            log "Tests passed on master branch, proceeding with production deployment..."
            deploy_production
        else
            log "Tests passed on ${BRANCH} branch"
        fi
        notify "SUCCESS" "CI process completed successfully"
    else
        notify "FAILURE" "CI process failed"
        exit 1
    fi
}

# Trap any errors and ensure cleanup happens
trap cleanup EXIT

# Run main function
main                                                                       