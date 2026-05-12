#!/bin/bash
# search-scraping - Remote Start Script
cd /home/opc/search-scraping/backend

# Virtualenv kontrolü
if [ ! -d "venv" ]; then
    echo "❌ venv bulunamadı! Lütfen önce kurulum yapın."
    exit 1
fi

source venv/bin/activate

# Mevcut süreçleri durdur
echo "🛑 Eski süreçler durduruluyor..."
pkill -f 'uvicorn api:app'
pkill -f 'python3 tracker.py'
sleep 2

# API'yi başlat
echo "🚀 API başlatılıyor..."
nohup uvicorn api:app --host 0.0.0.0 --port 8000 >> api_new.log 2>&1 &

# Tracker'ı başlat
echo "🔍 Takip sistemi başlatılıyor..."
nohup python3 tracker.py >> tracker_new.log 2>&1 &

echo "✅ Sistem arka planda çalışıyor."
ps aux | grep -E 'api:app|tracker.py'
