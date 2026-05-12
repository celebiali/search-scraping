#!/bin/bash

# Configuration
SERVER_IP="134.98.130.247"
SSH_KEY="e-commerce.key"
USER="opc"
REMOTE_PATH="/home/opc/search-scraping"

echo "🚀 Sunucuya bağlanılıyor: $SERVER_IP"

# Dosyaları gönder (node_modules ve pycache hariç)
rsync -avz -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o BatchMode=yes" \
    --exclude 'node_modules' \
    --exclude '.nuxt' \
    --exclude '.output' \
    --exclude '__pycache__' \
    --exclude 'tracking_system.db' \
    --exclude 'venv' \
    ./ $USER@$SERVER_IP:$REMOTE_PATH

# Sunucuda uygulamayı başlat
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o BatchMode=yes $USER@$SERVER_IP << 'EOF'
    cd /home/opc/search-scraping
    
    if command -v docker-compose &> /dev/null; then
        echo "🐳 Docker Compose kullanılıyor..."
        docker-compose down
        docker-compose up -d --build
    else
        echo "🏃 Manuel başlatma (nohup) kullanılıyor..."
        chmod +x scratch/remote_start.sh
        ./scratch/remote_start.sh
    fi
    echo "✅ Dağıtım tamamlandı!"
EOF
