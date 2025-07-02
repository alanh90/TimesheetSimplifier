#!/bin/bash

echo "Starting Timesheet Simplifier..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    echo
fi

# Create necessary directories
mkdir -p charge_codes data exports

# Start the application
echo "Starting Streamlit application..."
echo
echo "The application will open in your default browser."
echo "To stop the application, press Ctrl+C in this window."
echo
streamlit run app.py

# Deactivate virtual environment when done
deactivate