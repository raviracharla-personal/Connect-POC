@echo off
REM Navigates to the backend directory
cd /d "C:\connect\OfficerInsights\code-chatbot-option-1\backend"

REM (Optional but Recommended) Activate your Python virtual environment
REM If you have a venv folder, uncomment the next line
REM call venv\Scripts\activate

REM Start the Uvicorn server, listening on all interfaces on port 8000
echo "Starting Backend Server..."
uvicorn main:app --host 0.0.0.0 --port 8000