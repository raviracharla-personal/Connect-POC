@echo off
REM Navigates to the main frontend project directory
cd /d "C:\connect\OfficerInsights\code-chatbot-option-1\frontend"

REM Serve the production build from the /dist/frontend/browser folder on port 4200
REM The -s flag is crucial for single-page apps like Angular to handle routing correctly.
echo "Starting Frontend Server..."
REM serve -s dist/frontend/browser -l 4200
ng serve --open --host '0.0.0.0'