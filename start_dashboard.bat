@echo off
start /B python -m uvicorn src.dashboard:app --host 127.0.0.1 --port 8000 --workers 1 > nul 2>&1
echo Dashboard starting on http://127.0.0.1:8000
start http://127.0.0.1:8000