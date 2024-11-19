#!/bin/bash

# This script runs the pytest script test_weight_app.py

# Check if Python is installed
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
TEST_OUTPUT=$(pytest test_weight_app.py -v --maxfail=1 --disable-warnings --tb=short)

# Print the test results
echo "$TEST_OUTPUT"

# Extract the summary from pytest output using regex
SUMMARY=$(echo "$TEST_OUTPUT" | tail -n 10 | grep -E "^\=\=\=\=\=\=\=+")

# Extract the total number of tests, passed tests, and failed tests from the summary
PASSED_TESTS=$(echo "$SUMMARY" | grep -oP '\d+ passed' | awk '{print $1}')
FAILED_TESTS=$(echo "$SUMMARY" | grep -oP '\d+ failed' | awk '{print $1}')

# If any variable is empty, set it to 0
PASSED_TESTS=${PASSED_TESTS:-0}
FAILED_TESTS=${FAILED_TESTS:-0}
TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))

# Print a short summary
echo "Test Summary:"
echo "Total tests: $TOTAL_TESTS"
echo "Passed tests: $PASSED_TESTS"
echo "Failed tests: $FAILED_TESTS"

# If there are failed tests, return the number of failed tests as the exit code
if [[ "$FAILED_TESTS" -eq 0 ]]; then
    exit 0  # All tests passed
else
    # Return the number of failed tests as the exit code
    exit "$FAILED_TESTS"
fi
