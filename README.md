# Finora

Modern, Türkçe odaklı kişisel bütçe ve portföy yönetimi uygulaması.

Finora; gelir, sabit gider, taksit, kredi kartı, günlük harcama, periyodik işlemler ve yatırım takibini tek panelde birleştirir. Ayrıca yerel (kural tabanlı) AI danışman ile doğal dilden kayıt ekleme/güncelleme desteği sunar.

## Öne Çıkan Özellikler

- Gelir / gider / kredi kartı / taksit yönetimi
- Periyodik ödeme planlama ve yaklaşan işlemler görünümü
- Yatırım portföyü, canlı fiyat güncelleme ve kâr-zarar analizi
- Alacaklar listesi ve ürün takibi
- Türkçe doğal dil AI komutları (ekle, güncelle, taksit vb.)
- Responsive arayüz

## Gizlilik ve Veri Güvenliği

Finora **gizlilik odaklı** çalışır:

- Finansal kayıtlarınız uygulama içinde (yerel veritabanında) tutulur.
- AI danışman modülü kural tabanlıdır; finansal verileriniz LLM sağlayıcısına gönderilmez.
- `PRIVACY_MODE=1` (varsayılan) iken, kullanıcıdan alınan URL ile dış siteye fiyat çekme özelliği kapalıdır.

> Not: Canlı piyasa fiyatı servisleri (döviz/altın/borsa/kripto) aktif kullanımda yalnızca ilgili sembol/tip sorguları dış kaynağa gider; kişisel finansal tablolar gönderilmez.

## Teknoloji Yığını

- Python 3.11
- Flask
- SQLAlchemy
- Jinja2 + Vanilla JS + CSS
- Docker / Docker Compose

## Kurulum (Docker)

```bash
docker compose up --build -d
```

Uygulama:
- http://localhost:5000

## Ortam Değişkenleri

`docker-compose.yml` içinde:

- `FLASK_ENV=production`
- `PRIVACY_MODE=1` → gizlilik modu açık

Gizlilik modu kapatmak isterseniz:

- `PRIVACY_MODE=0`

## Proje Yapısı

- `app/app.py` → Flask uygulaması ve API uçları
- `app/ai_advisor.py` → kural tabanlı AI danışman
- `app/price_fetcher.py` → fiyat çekme/fallback akışları
- `app/templates/` → Jinja şablonları
- `app/static/` → CSS/JS/Favicon

## Lisans

Bu depo sahibinin belirleyeceği lisans koşullarına tabidir.
