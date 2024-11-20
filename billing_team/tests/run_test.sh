#!/bin/bash

# This script runs the pytest script test_weight_app.py

# Check if pytest is installed
if ! command -v pytest &>/dev/null; then
    echo "Pytest is not installed. Please install it first."
    exit 1
fi

# Navigate to the 'tests' directory
cd "$(dirname "$0")"  # This ensures we are in the 'tests' folder

# Set PYTHONPATH to the root of the project to ensure 'weight_app.py' is found
export PYTHONPATH=$(pwd)/..

# Echo message before running tests
echo "Running the tests..."

# Run pytest with the verbose option (-v), maxfail=1 to stop after the first failure, and disable warnings
TEST_OUTPUT=$(pytest test_add_truck.py -v --maxfail=1 --disable-warnings --tb=short)

# Print the test results
echo "$TEST_OUTPUT"

# If there are failed tests, return the number of failed tests as the exit code
if [[ "$FAILED_TESTS" -eq 0 ]]; then
    exit 0  # All tests passed
else
    # Return the number of failed tests as the exit code
    exit 1
fi