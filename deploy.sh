#!/bin/bash

# Configuration
SERVER_IP="134.98.130.247"
SSH_KEY="e-commerce.key"
USER="opc"
REMOTE_PATH="/home/opc/search-scraping"

echo "🚀 Sunucuya bağlanılıyor: $SERVER_IP"

# Dosyaları gönder (node_modules ve pycache hariç)
rsync -avz -e "ssh -i $SSH_KEY" \
    --exclude 'node_modules' \
    --exclude '.nuxt' \
    --exclude '.output' \
    --exclude '__pycache__' \
    --exclude 'tracking_system.db' \
    ./ $USER@$SERVER_IP:$REMOTE_PATH

# Sunucuda docker-compose çalıştır
ssh -i $SSH_KEY $USER@$SERVER_IP << 'EOF'
    cd /home/opc/search-scraping
    docker-compose down
    docker-compose up -d --build
    echo "✅ Dağıtım tamamlandı! Uygulama arka planda çalışıyor."
EOF
