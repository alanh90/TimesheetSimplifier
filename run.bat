@echo off
echo Starting Timesheet Simplifier...
echo.

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

REM Check if requirements are installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

REM Create necessary directories
if not exist "charge_codes" mkdir charge_codes
if not exist "data" mkdir data
if not exist "exports" mkdir exports

REM Start the application
echo Starting Streamlit application...
echo.
echo The application will open in your default browser.
echo To stop the application, press Ctrl+C in this window.
echo.
streamlit run app.py

REM Deactivate virtual environment when done
deactivate