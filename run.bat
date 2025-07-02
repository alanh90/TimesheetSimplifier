@echo off
echo Starting Timesheet Simplifier...
echo.

REM --- Virtual Environment Setup ---
REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM --- Dependency Installation ---
REM Always try to install/update requirements. This is more robust than checking for a single module.
echo Installing/Updating Python dependencies from requirements.txt...
pip install -r requirements.txt
echo.

REM --- Module Discovery for 'src' Directory ---
REM Add the 'src' directory to PYTHONPATH to allow imports like 'from src.models import ...'
REM %CD% gets the current working directory, which should be the project root.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
echo PYTHONPATH updated to include src\.
echo.

REM --- Directory Creation (for data/exports) ---
REM Create necessary directories if they don't already exist.
REM This ensures the app has places to store data and exports.
echo Ensuring necessary directories exist...
if not exist "charge_codes" mkdir charge_codes
if not exist "data" mkdir data
if not exist "exports" mkdir exports
echo Directories checked/created.
echo.

REM --- Start Streamlit Application ---
echo Starting Streamlit application...
echo.
echo The application will open in your default browser.
echo To stop the application, press Ctrl+C in this window.
echo.
REM Run the Streamlit app, specifying the path to app.py within src/
streamlit run src/app.py

REM --- Deactivate Virtual Environment ---
REM Deactivate virtual environment when the Streamlit app is stopped
deactivate
echo Virtual environment deactivated.