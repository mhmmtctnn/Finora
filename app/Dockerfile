# ── Build stage ──────────────────────────────────────────────────────
FROM python:3.11-slim

# Çalışma dizini
WORKDIR /app

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kaynak kodunu kopyala
COPY . .

# Veri tabanı dizini (persistent volume için)
RUN mkdir -p /app/instance

# Port
EXPOSE 5000

# Başlatma: gunicorn production server — preload ile tek seferinde init
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--preload", "app:app"]
