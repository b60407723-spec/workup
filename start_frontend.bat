@echo off
echo Starting English Word Memory System Frontend...
echo.
echo Frontend will be available at: http://localhost:8080
echo Press Ctrl+C to stop
echo.
cd frontend
python -m http.server 8080
