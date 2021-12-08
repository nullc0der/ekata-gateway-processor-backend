#!/bin/sh
echo "Starting arq worker..."
arq app.worker.WorkerSettings
