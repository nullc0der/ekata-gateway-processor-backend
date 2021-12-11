#!/bin/sh
echo "Starting server..."
gunicorn app.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
