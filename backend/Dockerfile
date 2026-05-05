FROM python:3.11-slim

WORKDIR /app

# ARM64 uyumluluğu için gerekli kütüphaneler
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hem API hem Tracker'ı başlatmak için bir script kullanabiliriz
# Ya da docker-compose'da ayrı servisler olarak tanımlayabiliriz.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
