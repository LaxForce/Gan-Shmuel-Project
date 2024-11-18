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

# Run the test_weight_app.py script
pytest test_weight_app.py