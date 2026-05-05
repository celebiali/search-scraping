#!/bin/bash

# Configuration
SERVER_IP="134.98.130.247"
SSH_KEY="e-commerce.key"
USER="opc"

echo "🛠️ Sunucu kurulumu başlatılıyor (Docker yükleniyor)..."

ssh -i $SSH_KEY $USER@$SERVER_IP << 'EOF'
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    # Docker Compose Plugin yükle
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-aarch64 -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    
    echo "✅ Docker ve Docker Compose başarıyla kuruldu!"
EOF
