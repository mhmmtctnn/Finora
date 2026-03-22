# Finora

Türkçe odaklı, modern bir kişisel finans yönetim platformu.

Finora; gelir, gider, kredi kartı, taksit, periyodik ödeme ve yatırım takibini tek bir panelde birleştirir. Uygulama, kural tabanlı AI danışman desteği ile doğal dil komutlarını finans kayıtlarına dönüştürür.

---

## Neden Finora?

- Çok modüllü finans takibi (gelir, sabit gider, günlük gider, taksit, kredi kartı)
- Portföy odaklı yatırım görünümü ve canlı fiyat güncelleme
- Türkçe AI komutları ile hızlı kayıt/güncelleme
- Mobil uyumlu, okunaklı ve operasyonel arayüz
- Gizlilik odaklı varsayılan yapı

---

## Özellikler

### Finans Modülleri
- Gelir yönetimi
- Sabit gider yönetimi
- Günlük gider (yol/yemek/diğer)
- Kredi kartı harcamaları
- Taksit planlama ve aylık yük görünümü
- Periyodik işlem planlama

### Yatırım Modülü
- Varlık bazlı portföy takibi
- Canlı birim fiyat çekme (tekil/toplu)
- Kâr/zarar ve maliyet analizi

### AI Destekli İşlem Akışları
- Doğal dilden gelir/gider/taksit ekleme
- Kayıt güncelleme akışları
- Yazım hatalarına toleranslı komut yorumlama

---

## Güvenlik ve Gizlilik

Finora varsayılan olarak gizlilik odaklı çalışır:

- Finansal veriler uygulama veritabanında tutulur.
- AI danışman akışı kural tabanlıdır.
- `PRIVACY_MODE=1` varsayılanı ile kullanıcı URL’si üzerinden dış ürün fiyatı çekme kapalıdır.

> Not: Canlı piyasa fiyatı (döviz/altın/borsa/kripto) sorgularında yalnızca varlık türü/sembol bilgisi dış kaynağa gider; finansal tablo içeriği gönderilmez.

---

## Teknoloji Yığını

- Python 3.11
- Flask + SQLAlchemy
- Jinja2 + Vanilla JavaScript + CSS
- Docker / Docker Compose

---

## Hızlı Başlangıç

```bash
docker compose up --build -d
```

Uygulama adresi: http://localhost:5000

---

## Ortam Değişkenleri

`docker-compose.yml`:

- `FLASK_ENV=production`
- `PRIVACY_MODE=1` (önerilen)

Gizlilik modunu kapatmak için:

- `PRIVACY_MODE=0`

---

## Proje Yapısı

- `app/app.py` — Flask app, route ve API katmanı
- `app/ai_advisor.py` — kural tabanlı AI danışman
- `app/price_fetcher.py` — fiyat çekme ve fallback akışları
- `app/templates/` — Jinja2 şablonları
- `app/static/` — CSS, JS, favicon

---

## Sürüm Geçmişi

Detaylı sürüm notları için: [CHANGELOG.md](CHANGELOG.md)

---

## Lisans

Bu proje, depo sahibinin belirleyeceği lisans koşullarına tabidir.
