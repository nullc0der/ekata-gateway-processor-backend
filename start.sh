#!/bin/sh
echo "Starting server..."
hypercorn app.app:app --bind 0.0.0.0:8000
