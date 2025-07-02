#!/bin/bash

echo "Starting Timesheet Simplifier..."
echo

# --- Virtual Environment Setup ---
# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    # Use 'python3' to ensure Python 3 is used if both python and python3 are present
    python3 -m venv venv
    echo "Virtual environment created."
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# --- Dependency Installation ---
# Always try to install/update requirements. This is more robust than checking for a single module.
echo "Installing/Updating Python dependencies from requirements.txt..."
pip install -r requirements.txt
echo

# --- Module Discovery for 'src' Directory ---
# Add the 'src' directory to PYTHONPATH to allow imports like 'from src.models import ...'
# $(pwd) gets the current working directory, which should be the project root.
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
echo "PYTHONPATH updated to include src/."
echo

# --- Directory Creation (for data/exports) ---
# Create necessary directories if they don't already exist.
# This ensures the app has places to store data and exports.
echo "Ensuring necessary directories exist..."
mkdir -p charge_codes data exports
echo "Directories checked/created."
echo

# --- Start Streamlit Application ---
echo "Starting Streamlit application..."
echo "The application will open in your default browser."
echo "To stop the application, press Ctrl+C in this window."
echo
# Run the Streamlit app, specifying the path to app.py within src/
streamlit run src/app.py

# --- Deactivate Virtual Environment ---
# Deactivate virtual environment when the Streamlit app is stopped
deactivate
echo "Virtual environment deactivated."