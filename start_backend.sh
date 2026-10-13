#!/bin/bash
echo "Starting English Word Memory System Backend..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
