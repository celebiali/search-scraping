#!/bin/bash
cd /home/opc/search-scraping/backend
source venv/bin/activate
pkill -f 'uvicorn api:app'
sleep 5
nohup uvicorn api:app --host 0.0.0.0 --port 8000 >> api_new.log 2>&1 &
echo "Server started in background"
