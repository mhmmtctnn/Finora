from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, date, timedelta
import os, json, re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///butce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'butceplan_secret_2026'
db = SQLAlchemy(app)

# ══════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════

class Gelir(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    baslik   = db.Column(db.String(200), nullable=False)
    miktar   = db.Column(db.Float, nullable=False)
    tip      = db.Column(db.String(50), default='maas')
    ay       = db.Column(db.Integer, nullable=False)
    yil      = db.Column(db.Integer, nullable=False)
    aciklama = db.Column(db.String(500))
    tarih    = db.Column(db.DateTime, default=datetime.now)

class SabitGider(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    tip      = db.Column(db.String(50), nullable=False)
    baslik   = db.Column(db.String(200), nullable=False)
    miktar   = db.Column(db.Float, nullable=False)
    ay       = db.Column(db.Integer, nullable=False)
    yil      = db.Column(db.Integer, nullable=False)
    aciklama = db.Column(db.String(500))
    tarih    = db.Column(db.DateTime, default=datetime.now)

class Taksit(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    baslik        = db.Column(db.String(200), nullable=False)
    toplam_miktar = db.Column(db.Float, nullable=False)
    taksit_sayisi = db.Column(db.Integer, nullable=False)
    aylik_odeme   = db.Column(db.Float, nullable=False)
    baslangic_ay  = db.Column(db.Integer, nullable=False)
    baslangic_yil = db.Column(db.Integer, nullable=False)
    bitis_ay      = db.Column(db.Integer, nullable=False)
    bitis_yil     = db.Column(db.Integer, nullable=False)
    aciklama      = db.Column(db.String(500))
    tarih         = db.Column(db.DateTime, default=datetime.now)

class KrediKarti(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    baslik   = db.Column(db.String(200), nullable=False)
    miktar   = db.Column(db.Float, nullable=False)
    kategori = db.Column(db.String(100))
    ay       = db.Column(db.Integer, nullable=False)
    yil      = db.Column(db.Integer, nullable=False)
    aciklama = db.Column(db.String(500))
    tarih    = db.Column(db.DateTime, default=datetime.now)

class GunlukGider(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    tip      = db.Column(db.String(50), nullable=False)
    baslik   = db.Column(db.String(200), nullable=False)
    miktar   = db.Column(db.Float, nullable=False)
    tarih    = db.Column(db.Date, default=date.today)
    aciklama = db.Column(db.String(500))

class Yatirim(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    tip         = db.Column(db.String(50), nullable=False)
    baslik      = db.Column(db.String(200), nullable=False)
    miktar      = db.Column(db.Float, nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    maliyet     = db.Column(db.Float, nullable=False)
    notlar      = db.Column(db.String(500))
    guncelleme  = db.Column(db.DateTime, default=datetime.now)
    tarih       = db.Column(db.DateTime, default=datetime.now)

    @property
    def mevcut_deger(self):
        return round(self.miktar * self.birim_fiyat, 2)

    @property
    def kar_zarar(self):
        return round(self.mevcut_deger - self.maliyet, 2)

    @property
    def kar_zarar_pct(self):
        return round((self.kar_zarar / self.maliyet * 100), 2) if self.maliyet > 0 else 0

class AlacakListesi(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    baslik        = db.Column(db.String(300), nullable=False)
    url           = db.Column(db.String(1000))
    fiyat         = db.Column(db.Float)
    taksit_sayisi = db.Column(db.Integer, default=1)
    kategori      = db.Column(db.String(100))
    oncelik       = db.Column(db.String(20), default='orta')
    durum         = db.Column(db.String(20), default='bekliyor')
    notlar        = db.Column(db.String(500))
    tarih         = db.Column(db.DateTime, default=datetime.now)

class AIChat(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    soru  = db.Column(db.Text, nullable=False)
    cevap = db.Column(db.Text, nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.now)

class AIPendingCommand(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    soru       = db.Column(db.Text, nullable=False)
    cmd_json   = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class PeriyodikIslem(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    tur           = db.Column(db.String(20), nullable=False, default='gider')  # gider | gelir
    kategori      = db.Column(db.String(50), nullable=False, default='diger')
    baslik        = db.Column(db.String(200), nullable=False)
    miktar        = db.Column(db.Float, nullable=False)
    periyot_ay    = db.Column(db.Integer, nullable=False, default=12)
    sonraki_tarih = db.Column(db.Date, nullable=False)
    aktif         = db.Column(db.Boolean, default=True)
    notlar        = db.Column(db.String(500))
    tarih         = db.Column(db.DateTime, default=datetime.now)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def get_ay_yil():
    n = datetime.now()
    return n.month, n.year

def get_last_n_months(n=6):
    now = datetime.now()
    months = []
    for i in range(n - 1, -1, -1):
        m, y = now.month - i, now.year
        while m <= 0:
            m += 12; y -= 1
        months.append((m, y))
    return months

def add_months(base_date: date, months: int) -> date:
    month = base_date.month - 1 + months
    year = base_date.year + month // 12
    month = month % 12 + 1
    day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                              31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def is_privacy_mode_enabled() -> bool:
    """Gizlilik modu: kullanıcı girdilerini dış servislere gönderen özellikleri kapatır."""
    return str(os.getenv('PRIVACY_MODE', '1')).strip().lower() in ['1', 'true', 'yes', 'on']


@app.template_filter('tr_tl')
def tr_tl(value):
    """29,000.00 -> 29.000 / 1234.5 -> 1.234,50"""
    try:
        n = float(value or 0)
    except Exception:
        return '0'

    # Tam sayıysa ondalık göstermeyelim
    if abs(n - round(n)) < 1e-9:
        return f"{int(round(n)):,}".replace(',', '.')

    s = f"{n:,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

def normalize_amount_string(raw: str) -> float:
    """Tutarları normalleştir: 120.000 / 120,000 / 120.000,50 / 120,000.50 / 500.00 / 500,00"""
    if ',' in raw and '.' in raw:
        if raw.rfind(',') > raw.rfind('.'):
            # TR: 120.000,50
            raw = raw.replace('.', '').replace(',', '.')
        else:
            # EN: 120,000.50
            raw = raw.replace(',', '')
    elif ',' in raw:
        parts = raw.split(',')
        if len(parts) == 2 and len(parts[1]) == 3:
            # 120,000
            raw = ''.join(parts)
        else:
            # 500,00
            raw = raw.replace(',', '.')
    elif '.' in raw:
        parts = raw.split('.')
        if len(parts) == 2 and len(parts[1]) == 3:
            # 120.000
            raw = ''.join(parts)
        # 500.00 ondalık formatı olduğu gibi kalır
    try:
        return float(raw)
    except Exception:
        return None

def parse_tl_amount(text: str):
    """İlk tutarı bul"""
    t = (text or '').lower().replace('₺', ' tl ')
    m = re.search(r'(\d{1,3}(?:[\.\s]\d{3})*(?:,\d+)?|\d+(?:,\d+)?)\s*(?:tl|lira)', t)
    if not m:
        return None
    raw = m.group(1).replace(' ', '')
    return normalize_amount_string(raw)

def parse_all_tl_amounts(text: str):
    """Tüm tutarları bul (çoklu telefon faturası vs.)"""
    t = (text or '').lower().replace('₺', ' tl ')
    pattern = r'(\d{1,3}(?:[\.\s]\d{3})*(?:,\d+)?|\d+(?:,\d+)?)\s*(?:tl|lira)'
    matches = re.findall(pattern, t)
    
    amounts = []
    for raw in matches:
        raw = raw.replace(' ', '')
        amount = normalize_amount_string(raw)
        if amount and amount > 0:
            amounts.append(amount)
    
    return amounts if amounts else None

def parse_all_amounts_loose(text: str):
    """TL/lira yazılmasa da metindeki sayısal tutar adaylarını bulur (güncelle komutları için)."""
    t = (text or '').lower().replace('₺', ' ')
    pattern = r'(\d{1,3}(?:[\.\s]\d{3})*(?:,\d+)?|\d+(?:[\.,]\d+)?)'
    matches = re.findall(pattern, t)

    amounts = []
    for raw in matches:
        raw = raw.replace(' ', '')
        amount = normalize_amount_string(raw)
        if amount and amount > 0:
            amounts.append(amount)

    return amounts if amounts else None

def parse_taksit_count(text: str):
    t = (text or '').lower()
    # Taksit: "9 taksit", "taksit 9", vb.
    m = re.search(r'(\d+)\s*taks\w*', t)
    if m:
        return int(m.group(1))
    m = re.search(r'taks\w*\s*(\d+)', t)
    if m:
        return int(m.group(1))
    # Ay cinsinden taksit: "5 ay boyunca", "5 aylık", vb. (taksit bağlamında)
    if any(k in t for k in ['taksit', 'taks', 'ödeme planı', 'odeme plani']):
        m = re.search(r'(\d+)\s*(?:ay|aylık|aylik|aylar|aylik)', t)
        if m:
            return int(m.group(1))
    return None

def parse_period_months(text: str):
    t = (text or '').lower()
    if any(k in t for k in ['yıllık', 'yillik', 'senelik', 'yılda bir', 'yilda bir']):
        return 12
    if any(k in t for k in ['6 ay', 'altı ay', 'alti ay']):
        return 6
    if any(k in t for k in ['3 ay', 'üç ay', 'uc ay']):
        return 3
    if any(k in t for k in ['aylık', 'aylik', 'her ay']):
        return 1
    m = re.search(r'(\d+)\s*ay', t)
    if m:
        return max(1, int(m.group(1)))
    return 12

def parse_next_date(text: str):
    t = (text or '').lower()
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', t)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    m = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', t)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except Exception:
            pass

    ay_map = {
        'ocak': 1, 'şubat': 2, 'subat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'mayis': 5, 'haziran': 6,
        'temmuz': 7, 'ağustos': 8, 'agustos': 8, 'eylül': 9, 'eylul': 9, 'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12,
    }
    for ad, no in ay_map.items():
        if ad in t:
            yil_m = re.search(r'(20\d{2})', t)
            y = int(yil_m.group(1)) if yil_m else datetime.now().year
            d = date(y, no, min(date.today().day, 28))
            if d < date.today():
                d = date(y + 1, no, min(date.today().day, 28))
            return d
    return date.today() + timedelta(days=30)


def infer_expense_meta(q: str):
    """Gider metninden tip ve başlık çıkar."""
    t = (q or '').lower()

    rules = [
        (['doğalgaz', 'dogalgaz'], 'dogalgaz', 'Doğalgaz Faturası'),
        (['elektrik'], 'elektrik', 'Elektrik Faturası'),
        (['internet'], 'internet', 'İnternet Faturası'),
        (['telefon', 'gsm', 'hat'], 'telefon', 'Telefon Faturası'),
        (['su'], 'su', 'Su Faturası'),
        (['kira'], 'kira', 'Kira Gideri'),
        (['aidat'], 'aidat', 'Aidat Gideri'),
        (['yakıt', 'yakit', 'benzin', 'mazot'], 'ulasim', 'Yakıt Gideri'),
        (['market', 'manav', 'migros', 'a101', 'bim', 'şok', 'sok'], 'market', 'Market Gideri'),
        (['fatura'], 'fatura', 'Fatura Gideri'),
    ]

    for kws, tip, baslik in rules:
        if any(k in t for k in kws):
            return tip, baslik

    return 'diger', 'AI ile eklenen gider'

def parse_ai_finance_command(text: str):
    q = (text or '').lower()
    amount = parse_tl_amount(q)
    amounts = parse_all_tl_amounts(q)  # Tüm tutarları al
    taksit_sayi = parse_taksit_count(q)

    gelir_kelimeleri = ['gelir', 'tahsil', 'alacağım', 'alacagim', 'prim', 'komisyon', 'ödenecek', 'odenek', 'maaş', 'maas']
    gider_kelimeleri = ['harcama', 'alışveriş', 'alisveris', 'borç', 'borc', 'ödeme', 'odeme', 'kredi', 'fatura', 'mobılya', 'mobilya']
    is_income = any(k in q for k in gelir_kelimeleri)
    is_expense = any(k in q for k in gider_kelimeleri)
    has_add_cmd = any(k in q for k in ['ekle', 'kaydet', 'tanımla', 'tanimla', 'işle', 'isle', 'yaz', 'gir', 'girer misin'])
    has_update_cmd = any(k in q for k in ['güncelle', 'guncelle', 'düzelt', 'duzelt', 'revize', 'değiştir', 'degistir'])
    taksit_ifadesi = any(k in q for k in ['taks', 'ay boyunca', 'ay boyu', 'aylık ödeme', 'aylik odeme', 'taksitlendirme', 'taksitle'])

    # Mevcut sabit gideri güncelleme (örn: "39.00 TL eklenmiş, 39.000 TL olarak güncelle")
    if has_update_cmd and (is_expense or any(k in q for k in ['harcama', 'gider', 'fatura', 'ev', 'kira', 'telefon'])):
        amount_list = amounts or []
        if len(amount_list) < 2:
            loose = parse_all_amounts_loose(q) or []
            if len(loose) >= 2:
                amount_list = loose

        if not amount_list:
            return None

        old_amount = amount_list[0] if len(amount_list) >= 2 else None
        new_amount = amount_list[-1]

        tip = None
        if 'kira' in q:
            tip = 'kira'
        elif 'elektrik' in q:
            tip = 'elektrik'
        elif 'su' in q:
            tip = 'su'
        elif 'internet' in q:
            tip = 'internet'
        elif 'aidat' in q:
            tip = 'aidat'
        elif 'telefon' in q:
            tip = 'telefon'

        return {
            'action': 'sabit_gider_guncelle',
            'tip': tip,
            'old_miktar': old_amount,
            'new_miktar': new_amount,
            'keyword': 'ev' if 'ev' in q else ('telefon' if 'telefon' in q else None),
            'query': q,
        }

    if taksit_sayi and amount and (taksit_ifadesi or (is_expense and ('mobılya' in q or 'mobilya' in q))):
        baslik = 'AI ile eklenen taksit'
        if 'telefon' in q: baslik = 'Telefon alışverişi'
        elif 'araba' in q or 'araç' in q or 'arac' in q: baslik = 'Araç harcaması'
        elif 'ev' in q: baslik = 'Ev alışverişi'
        elif 'mobılya' in q or 'mobilya' in q: baslik = 'Mobilya alışverişi'

        return {
            'action': 'gelir_taksit' if is_income and not is_expense else 'gider_taksit',
            'baslik': baslik,
            'toplam_miktar': amount,
            'taksit_sayisi': taksit_sayi,
        }

    periyodik_anahtar = ['sigorta', 'kasko', 'mtv', 'motorlu taşıtlar vergisi', 'motorlu tasitlar vergisi', 'vergi', 'bandrol', 'yenilenecek', 'yenilenecek']
    if any(k in q for k in periyodik_anahtar) and amount:
        kategori = 'diger'
        if 'sigorta' in q: kategori = 'trafik_sigortasi'
        elif 'kasko' in q: kategori = 'kasko'
        elif 'mtv' in q or 'motorlu taşıtlar vergisi' in q or 'motorlu tasitlar vergisi' in q: kategori = 'mtv'
        elif 'vergi' in q: kategori = 'vergi'

        return {
            'action': 'periyodik',
            'tur': 'gelir' if is_income and not is_expense else 'gider',
            'kategori': kategori,
            'baslik': 'AI ile eklenen periyodik işlem',
            'miktar': amount,
            'periyot_ay': parse_period_months(q),
            'sonraki_tarih': parse_next_date(q),
        }

    # Çoklu tutarlar (ör: "700 TL ve 850 TL telefon faturası her ay")
    if amounts and len(amounts) > 1 and (has_add_cmd or (is_expense and 'fatura' in q)):
        total_amount = sum(amounts)
        tip, baslik = infer_expense_meta(q)
        return {
            'action': 'sabit_gider_tek',
            'baslik': baslik,
            'tip': tip,
            'miktar': total_amount,
            'aciklama': f"Çoklu tutarlar: {' + '.join(f'{a:.2f}' for a in amounts)} TL"
        }

    # Tek seferlik / aylık gelir-gider ekleme (AI sohbetinden)
    if amount and has_add_cmd:
        if is_income or any(k in q for k in ['aylık gelir', 'aylik gelir', 'gelirim', 'maaşım', 'maasim', 'maaş', 'maas']):
            tip = 'maas' if any(k in q for k in ['maaş', 'maas']) else 'ek_gelir'
            baslik = 'AI ile eklenen gelir'
            if 'maaş' in q or 'maas' in q:
                baslik = 'Maaş Geliri'
            elif 'kira' in q:
                baslik = 'Kira Geliri'
                tip = 'kira_geliri'
            elif 'prim' in q:
                baslik = 'Prim Geliri'

            return {
                'action': 'gelir_tek',
                'baslik': baslik,
                'tip': tip,
                'miktar': amount,
            }

        if is_expense or any(k in q for k in ['gider', 'masraf', 'fatura', 'kira', 'elektrik', 'su', 'internet']):
            tip, baslik = infer_expense_meta(q)

            return {
                'action': 'sabit_gider_tek',
                'baslik': baslik,
                'tip': tip,
                'miktar': amount,
            }

    return None

def is_ai_confirm_text(text: str) -> bool:
    q = (text or '').strip().lower()
    return q in ['onay', 'onayla', 'evet', 'tamam', 'devam', 'uygula']

def is_ai_cancel_text(text: str) -> bool:
    q = (text or '').strip().lower()
    return q in ['iptal', 'vazgeç', 'vazgec', 'hayır', 'hayir', 'dur']

def format_ai_cmd_preview(cmd):
    if not cmd:
        return 'İşlem özeti bulunamadı.'

    action = cmd.get('action')
    if action == 'gelir_tek':
        return f"💰 Gelir eklenecek: {float(cmd.get('miktar', 0)):,.2f} ₺ ({cmd.get('baslik', 'Gelir')})"
    if action == 'sabit_gider_tek':
        return f"💸 Sabit gider eklenecek: {float(cmd.get('miktar', 0)):,.2f} ₺ ({cmd.get('baslik', 'Gider')})"
    if action == 'gider_taksit':
        sayi = int(cmd.get('taksit_sayisi', 1) or 1)
        toplam = float(cmd.get('toplam_miktar', 0) or 0)
        aylik = round(toplam / sayi, 2) if sayi > 0 else toplam
        return f"📆 Gider taksiti eklenecek: {toplam:,.2f} ₺ / {sayi} ay (aylık {aylik:,.2f} ₺)"
    if action == 'gelir_taksit':
        sayi = int(cmd.get('taksit_sayisi', 1) or 1)
        toplam = float(cmd.get('toplam_miktar', 0) or 0)
        aylik = round(toplam / sayi, 2) if sayi > 0 else toplam
        return f"📆 Gelir planı eklenecek: {toplam:,.2f} ₺ / {sayi} ay (aylık {aylik:,.2f} ₺)"
    if action == 'periyodik':
        tur = 'gelir' if cmd.get('tur') == 'gelir' else 'gider'
        return f"🔁 Periyodik {tur} eklenecek: {float(cmd.get('miktar', 0)):,.2f} ₺, {int(cmd.get('periyot_ay', 12))} ayda bir"

    return 'İşlem algılandı.'

def apply_ai_finance_command(cmd):
    if not cmd:
        return None
    ay, yil = get_ay_yil()

    if cmd['action'] == 'gider_taksit':
        sayi = int(cmd['taksit_sayisi'])
        toplam = float(cmd['toplam_miktar'])
        bas_ay, bas_yil = ay, yil
        bit_ay = (bas_ay - 1 + sayi - 1) % 12 + 1
        bit_yil = bas_yil + (bas_ay - 1 + sayi - 1) // 12
        t = Taksit(
            baslik=cmd['baslik'],
            toplam_miktar=toplam,
            taksit_sayisi=sayi,
            aylik_odeme=round(toplam / sayi, 2),
            baslangic_ay=bas_ay,
            baslangic_yil=bas_yil,
            bitis_ay=bit_ay,
            bitis_yil=bit_yil,
            aciklama='AI sohbetinden otomatik eklendi'
        )
        db.session.add(t)
        db.session.commit()
        return f"✅ {toplam:,.2f} ₺ tutarlı, {sayi} taksitlik gider uygulamaya eklendi."

    if cmd['action'] == 'gelir_taksit':
        sayi = int(cmd['taksit_sayisi'])
        toplam = float(cmd['toplam_miktar'])
        aylik = round(toplam / sayi, 2)
        now = date.today()
        for i in range(sayi):
            d = add_months(now, i)
            g = Gelir(
                baslik=f"{cmd['baslik']} (AI gelir taksiti {i+1}/{sayi})",
                miktar=aylik,
                tip='taksit_gelir',
                ay=d.month,
                yil=d.year,
                aciklama='AI sohbetinden otomatik planlandı'
            )
            db.session.add(g)
        db.session.commit()
        return f"✅ {toplam:,.2f} ₺ toplamlı {sayi} parçalı gelir planı oluşturuldu (aylık {aylik:,.2f} ₺)."

    if cmd['action'] == 'periyodik':
        p = PeriyodikIslem(
            tur=cmd['tur'],
            kategori=cmd['kategori'],
            baslik=cmd['baslik'],
            miktar=float(cmd['miktar']),
            periyot_ay=int(cmd['periyot_ay']),
            sonraki_tarih=cmd['sonraki_tarih'],
            notlar='AI sohbetinden otomatik eklendi'
        )
        db.session.add(p)
        db.session.commit()
        return f"✅ Periyodik {'gelir' if p.tur == 'gelir' else 'gider'} eklendi: {p.baslik} — {p.sonraki_tarih.strftime('%d.%m.%Y')} tarihinde hatırlatılacak."

    if cmd['action'] == 'gelir_tek':
        g = Gelir(
            baslik=cmd['baslik'],
            miktar=float(cmd['miktar']),
            tip=cmd.get('tip', 'ek_gelir'),
            ay=ay,
            yil=yil,
            aciklama='AI sohbetinden otomatik eklendi'
        )
        db.session.add(g)
        db.session.commit()
        return f"✅ Aylık gelirinize {g.miktar:,.2f} ₺ eklendi ({g.baslik})."

    if cmd['action'] == 'sabit_gider_tek':
        s = SabitGider(
            tip=cmd.get('tip', 'diger'),
            baslik=cmd['baslik'],
            miktar=float(cmd['miktar']),
            ay=ay,
            yil=yil,
            aciklama=cmd.get('aciklama', 'AI sohbetinden otomatik eklendi')
        )
        db.session.add(s)
        db.session.commit()
        return f"✅ Aylık giderlerinize {s.miktar:,.2f} ₺ eklendi ({s.baslik})."

    if cmd['action'] == 'sabit_gider_guncelle':
        old_miktar = cmd.get('old_miktar')
        new_miktar = float(cmd.get('new_miktar') or 0)
        hedef_tip = cmd.get('tip')
        keyword = (cmd.get('keyword') or '').lower()

        adaylar = SabitGider.query.filter_by(ay=ay, yil=yil).order_by(SabitGider.tarih.desc()).all()

        old_eleme = adaylar
        if old_miktar is not None:
            old_eleme = [x for x in adaylar if abs(float(x.miktar) - float(old_miktar)) < 0.01]
            if old_eleme:
                adaylar = old_eleme

        if hedef_tip:
            tip_eleme = [x for x in adaylar if x.tip == hedef_tip or hedef_tip in (x.baslik or '').lower()]
            if tip_eleme:
                adaylar = tip_eleme

        if keyword:
            key_eleme = [
                x for x in adaylar
                if keyword in (x.baslik or '').lower() or keyword in (x.aciklama or '').lower()
            ]
            if key_eleme:
                adaylar = key_eleme

        secilen = None
        if adaylar:
            secilen = adaylar[0]

        if not secilen:
            return "⚠️ Güncellenecek uygun sabit gider bulunamadı. Lütfen başlığı da yazarak tekrar deneyin."

        onceki = float(secilen.miktar)
        secilen.miktar = new_miktar
        if secilen.aciklama:
            secilen.aciklama = f"{secilen.aciklama} | AI güncelleme: {onceki:,.2f} -> {new_miktar:,.2f}"
        else:
            secilen.aciklama = f"AI güncelleme: {onceki:,.2f} -> {new_miktar:,.2f}"
        db.session.commit()
        return f"✅ '{secilen.baslik}' gideri {onceki:,.2f} ₺ → {new_miktar:,.2f} ₺ olarak güncellendi."

    return None

def yaklasan_periyodikler(days=120):
    bugun = date.today()
    sinir = bugun + timedelta(days=days)
    return PeriyodikIslem.query.filter(
        PeriyodikIslem.aktif == True,
        PeriyodikIslem.sonraki_tarih >= bugun,
        PeriyodikIslem.sonraki_tarih <= sinir,
    ).order_by(PeriyodikIslem.sonraki_tarih.asc()).all()

def aylik_ozet(ay, yil):
    tg = db.session.query(func.coalesce(func.sum(Gelir.miktar), 0.0)).filter_by(ay=ay, yil=yil).scalar() or 0.0
    ts = db.session.query(func.coalesce(func.sum(SabitGider.miktar), 0.0)).filter_by(ay=ay, yil=yil).scalar() or 0.0
    tt = db.session.query(func.coalesce(func.sum(Taksit.aylik_odeme), 0.0)).filter(
        (Taksit.baslangic_yil * 12 + Taksit.baslangic_ay) <= (yil * 12 + ay),
        (Taksit.bitis_yil    * 12 + Taksit.bitis_ay)      >= (yil * 12 + ay)
    ).scalar() or 0.0
    tk = db.session.query(func.coalesce(func.sum(KrediKarti.miktar), 0.0)).filter_by(ay=ay, yil=yil).scalar() or 0.0

    gunluk_rows = db.session.query(
        GunlukGider.tip,
        func.coalesce(func.sum(GunlukGider.miktar), 0.0)
    ).filter(
        db.extract('month', GunlukGider.tarih) == ay,
        db.extract('year',  GunlukGider.tarih) == yil
    ).group_by(GunlukGider.tip).all()
    gunluk_map = {tip: float(total or 0.0) for tip, total in gunluk_rows}

    periyodik_rows = db.session.query(
        PeriyodikIslem.tur,
        func.coalesce(func.sum(PeriyodikIslem.miktar), 0.0)
    ).filter(
        PeriyodikIslem.aktif == True,
        db.extract('month', PeriyodikIslem.sonraki_tarih) == ay,
        db.extract('year',  PeriyodikIslem.sonraki_tarih) == yil
    ).group_by(PeriyodikIslem.tur).all()
    periyodik_map = {tur: float(total or 0.0) for tur, total in periyodik_rows}

    tyol = gunluk_map.get('yol', 0.0)
    tyemek = gunluk_map.get('yemek', 0.0)
    tdiger = gunluk_map.get('diger', 0.0)
    tper_gider = periyodik_map.get('gider', 0.0)
    tper_gelir = periyodik_map.get('gelir', 0.0)

    tyatirim_deger = db.session.query(
        func.coalesce(func.sum(Yatirim.miktar * Yatirim.birim_fiyat), 0.0)
    ).scalar() or 0.0
    tyatirim_maliyet = db.session.query(
        func.coalesce(func.sum(Yatirim.maliyet), 0.0)
    ).scalar() or 0.0

    tg += tper_gelir
    toplam_gider = ts + tt + tk + tyol + tyemek + tdiger + tper_gider

    return dict(
        toplam_gelir=tg, toplam_sabit=ts, toplam_taksit=tt,
        toplam_kredi=tk, toplam_yol=tyol, toplam_yemek=tyemek,
        toplam_diger=tdiger,
        toplam_periyodik_gider=tper_gider,
        toplam_periyodik_gelir=tper_gelir,
        toplam_gider=toplam_gider,
        toplam_yatirim_deger=tyatirim_deger,
        toplam_yatirim_maliyet=tyatirim_maliyet,
        kalan=tg - toplam_gider
    )

@app.context_processor
def inject_globals():
    return {'now': datetime.now(), 'current_path': request.path}

# ══════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════

@app.route('/')
def dashboard():
    ay, yil = get_ay_yil()
    ozet = aylik_ozet(ay, yil)
    yaklasanlar = yaklasan_periyodikler(120)
    return render_template('dashboard.html', ozet=ozet, ay=ay, yil=yil, yaklasanlar=yaklasanlar)

@app.route('/gelirler')
def gelirler_sayfasi():
    ay, yil = get_ay_yil()
    gelirler = Gelir.query.filter_by(ay=ay, yil=yil).order_by(Gelir.tarih.desc()).all()
    return render_template('gelirler.html', gelirler=gelirler, ay=ay, yil=yil)

@app.route('/sabit-giderler')
def sabit_giderler_sayfasi():
    ay, yil = get_ay_yil()
    giderler = SabitGider.query.filter_by(ay=ay, yil=yil).order_by(SabitGider.tip).all()
    return render_template('sabit_giderler.html', giderler=giderler, ay=ay, yil=yil)

@app.route('/taksitler')
def taksitler_sayfasi():
    ay, yil = get_ay_yil()
    taksitler = Taksit.query.order_by(Taksit.tarih.desc()).all()
    return render_template('taksitler.html', taksitler=taksitler, ay=ay, yil=yil)

@app.route('/kredi-karti')
def kredi_karti_sayfasi():
    ay, yil = get_ay_yil()
    harcamalar = KrediKarti.query.filter_by(ay=ay, yil=yil).order_by(KrediKarti.tarih.desc()).all()
    return render_template('kredi_karti.html', harcamalar=harcamalar, ay=ay, yil=yil)

@app.route('/gunluk-giderler')
def gunluk_giderler_sayfasi():
    bugun = date.today()
    giderler = GunlukGider.query.filter_by(tarih=bugun).order_by(GunlukGider.id.desc()).all()
    return render_template('gunluk_giderler.html', giderler=giderler, bugun=bugun)

@app.route('/yatirimlar')
def yatirimlar_sayfasi():
    yatirimlar = Yatirim.query.order_by(Yatirim.tip, Yatirim.baslik).all()
    tip_ikonu = {'dolar':'💵','euro':'💶','altin':'🥇','gumus':'🥈',
                 'borsa':'📈','kripto':'₿','diger':'📦'}
    return render_template('yatirimlar.html', yatirimlar=yatirimlar, tip_ikonu=tip_ikonu)

@app.route('/alacaklar')
def alacaklar_sayfasi():
    ay, yil = get_ay_yil()
    ozet = aylik_ozet(ay, yil)
    items = AlacakListesi.query.order_by(
        AlacakListesi.durum, AlacakListesi.oncelik.desc(), AlacakListesi.tarih.desc()
    ).all()
    return render_template('alacaklar.html', alacaklar=items, ozet=ozet)

@app.route('/periyodikler')
def periyodikler_sayfasi():
    kayitlar = PeriyodikIslem.query.order_by(PeriyodikIslem.sonraki_tarih.asc()).all()
    return render_template('periyodikler.html', kayitlar=kayitlar)

@app.route('/ai-danisma')
def ai_danisma_sayfasi():
    gecmis = AIChat.query.order_by(AIChat.tarih.asc()).limit(50).all()
    ay, yil = get_ay_yil()
    ozet = aylik_ozet(ay, yil)
    from ai_advisor import calculate_health_score
    skor, feedback = calculate_health_score({
        'gelir': ozet['toplam_gelir'],
        'gider': ozet['toplam_gider'],
        'taksit': ozet['toplam_taksit'],
        'yatirim_deger': ozet['toplam_yatirim_deger'],
    })
    oneriler = [
        '120.000 TL alışverişim vardı, 3 taksit kaldı. Uygulamaya ekle.',
        'Yıllık trafik sigortam 15.000 TL, Eylül ayında yenilenecek. Hatırlat.',
        'Araba MTV vergim 8.000 TL, her yıl Ocak ayında yenileniyor.',
        '60.000 TL gelir alacağım var, 3 taksitte tahsil edilecek. Kaydet.',
        'bütçe analizi', 'finansal sağlık'
    ]
    return render_template('ai_danisma.html', gecmis=gecmis, ozet=ozet, skor=skor, feedback=feedback, oneriler=oneriler)

# ══════════════════════════════════════════════════════════════════════
# API — GELİR
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/gelir', methods=['POST'])
def gelir_ekle():
    d = request.json
    ay, yil = get_ay_yil()
    g = Gelir(baslik=d['baslik'], miktar=float(d['miktar']),
              tip=d.get('tip','maas'), ay=d.get('ay',ay), yil=d.get('yil',yil),
              aciklama=d.get('aciklama',''))
    db.session.add(g); db.session.commit()
    return jsonify({'ok': True, 'id': g.id})

@app.route('/api/gelir/<int:gid>', methods=['DELETE'])
def gelir_sil(gid):
    g = Gelir.query.get_or_404(gid)
    db.session.delete(g); db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════════════
# API — SABİT GİDER
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/sabit-gider', methods=['POST'])
def sabit_gider_ekle():
    d = request.json
    ay, yil = get_ay_yil()
    g = SabitGider(tip=d['tip'], baslik=d['baslik'], miktar=float(d['miktar']),
                   ay=d.get('ay',ay), yil=d.get('yil',yil), aciklama=d.get('aciklama',''))
    db.session.add(g); db.session.commit()
    return jsonify({'ok': True, 'id': g.id})

@app.route('/api/sabit-gider/<int:gid>', methods=['DELETE'])
def sabit_gider_sil(gid):
    g = SabitGider.query.get_or_404(gid)
    db.session.delete(g); db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════════════
# API — TAKSİT
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/taksit', methods=['POST'])
def taksit_ekle():
    d = request.json
    ay, yil = get_ay_yil()
    bas_ay  = int(d.get('baslangic_ay', ay))
    bas_yil = int(d.get('baslangic_yil', yil))
    sayi    = int(d['taksit_sayisi'])
    aylik   = float(d['toplam_miktar']) / sayi
    bit_ay  = (bas_ay - 1 + sayi - 1) % 12 + 1
    bit_yil = bas_yil + (bas_ay - 1 + sayi - 1) // 12
    t = Taksit(baslik=d['baslik'], toplam_miktar=float(d['toplam_miktar']),
               taksit_sayisi=sayi, aylik_odeme=round(aylik,2),
               baslangic_ay=bas_ay, baslangic_yil=bas_yil,
               bitis_ay=bit_ay, bitis_yil=bit_yil, aciklama=d.get('aciklama',''))
    db.session.add(t); db.session.commit()
    return jsonify({'ok': True, 'id': t.id})

@app.route('/api/taksit/<int:tid>', methods=['DELETE'])
def taksit_sil(tid):
    t = Taksit.query.get_or_404(tid)
    db.session.delete(t); db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════════════
# API — KREDİ KARTI
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/kredi-karti', methods=['POST'])
def kredi_karti_ekle():
    d = request.json
    ay, yil = get_ay_yil()
    k = KrediKarti(baslik=d['baslik'], miktar=float(d['miktar']),
                   kategori=d.get('kategori',''), ay=d.get('ay',ay), yil=d.get('yil',yil),
                   aciklama=d.get('aciklama',''))
    db.session.add(k); db.session.commit()
    return jsonify({'ok': True, 'id': k.id})

@app.route('/api/kredi-karti/<int:kid>', methods=['DELETE'])
def kredi_karti_sil(kid):
    k = KrediKarti.query.get_or_404(kid)
    db.session.delete(k); db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════════════
# API — GÜNLÜK GİDER
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/gunluk-gider', methods=['POST'])
def gunluk_gider_ekle():
    d = request.json
    g = GunlukGider(tip=d['tip'], baslik=d['baslik'], miktar=float(d['miktar']),
                    tarih=date.fromisoformat(d['tarih']) if d.get('tarih') else date.today(),
                    aciklama=d.get('aciklama',''))
    db.session.add(g); db.session.commit()
    return jsonify({'ok': True, 'id': g.id})

@app.route('/api/gunluk-gider/<int:gid>', methods=['DELETE'])
def gunluk_gider_sil(gid):
    g = GunlukGider.query.get_or_404(gid)
    db.session.delete(g); db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════════════
# API — YATIRIM
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/yatirim', methods=['POST'])
def yatirim_ekle():
    d = request.json
    miktar = float(d['miktar'])
    birim  = float(d['birim_fiyat'])
    tip    = (d.get('tip') or '').strip().lower()
    sembol = (d.get('sembol') or '').strip().upper()

    # Türe göre canlı birim fiyatı öncelikli dene
    try:
        from price_fetcher import fetch_asset_price
        canlı = fetch_asset_price(tip, sembol)
        if canlı.get('ok') and canlı.get('birim_fiyat'):
            birim = float(canlı['birim_fiyat'])
    except Exception:
        pass

    notlar = d.get('notlar','')
    if sembol:
        sym_tag = f"[SYM:{sembol}]"
        if sym_tag not in notlar:
            notlar = f"{sym_tag} {notlar}".strip()

    y = Yatirim(tip=d['tip'], baslik=d['baslik'], miktar=miktar,
                birim_fiyat=birim, maliyet=float(d.get('maliyet', miktar * birim)),
                notlar=notlar)
    db.session.add(y); db.session.commit()
    return jsonify({'ok': True, 'id': y.id,
                    'mevcut_deger': y.mevcut_deger, 'kar_zarar': y.kar_zarar})

@app.route('/api/yatirim/<int:yid>', methods=['PUT'])
def yatirim_guncelle(yid):
    y = Yatirim.query.get_or_404(yid)
    d = request.json

    if 'tip' in d:
        tip = (d.get('tip') or '').strip().lower()
        if tip in ['hisse', 'hisse_senedi', 'hisse-senedi']:
            tip = 'borsa'
        gecerli_tipler = {'dolar', 'euro', 'altin', 'gumus', 'borsa', 'kripto', 'diger'}
        if tip in gecerli_tipler:
            y.tip = tip

    if 'baslik' in d and d.get('baslik'):
        y.baslik = d['baslik'].strip()

    if 'birim_fiyat' in d:
        y.birim_fiyat = float(d['birim_fiyat'])
        y.guncelleme  = datetime.now()
    if 'miktar' in d:
        y.miktar = float(d['miktar'])
    db.session.commit()
    return jsonify({'ok': True, 'mevcut_deger': y.mevcut_deger, 'kar_zarar': y.kar_zarar,
                    'kar_zarar_pct': y.kar_zarar_pct})

@app.route('/api/yatirim/<int:yid>', methods=['DELETE'])
def yatirim_sil(yid):
    y = Yatirim.query.get_or_404(yid)
    db.session.delete(y); db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/yatirim/canli-fiyat')
def canli_fiyat():
    from price_fetcher import fetch_live_prices
    return jsonify(fetch_live_prices())

@app.route('/api/yatirim/tek-fiyat', methods=['POST'])
def yatirim_tek_fiyat():
    d = request.json or {}
    tip = (d.get('tip') or '').strip().lower()
    sembol = (d.get('sembol') or '').strip()
    from price_fetcher import fetch_asset_price
    return jsonify(fetch_asset_price(tip, sembol))

@app.route('/api/yatirim/canli-guncelle', methods=['POST'])
def yatirim_canli_guncelle():
    """Mevcut yatırım kayıtlarının birim fiyatını canlı veriden toplu günceller."""
    from price_fetcher import fetch_asset_price

    kayitlar = Yatirim.query.order_by(Yatirim.id.asc()).all()
    guncellenen = 0
    atlanan = 0
    detaylar = []

    for y in kayitlar:
        tip = (y.tip or '').lower()

        sembol = ''
        if tip in ['borsa', 'kripto']:
            # Önce notlardaki [SYM:XXX] etiketini dene
            mtag = re.search(r'\[SYM:([A-Z0-9\-\.]{2,16})\]', (y.notlar or '').upper())
            if mtag:
                sembol = mtag.group(1)

            # Bulunamazsa başlıktan olası sembolü çıkar (örn: THYAO, BTC)
            baslik = (y.baslik or '').strip().upper()
            if not sembol:
                m = re.search(r'[A-Z0-9\-\.]{2,12}', baslik)
                sembol = m.group(0) if m else baslik

        sonuc = fetch_asset_price(tip, sembol)
        if sonuc.get('ok') and sonuc.get('birim_fiyat'):
            eski = float(y.birim_fiyat)
            yeni = float(sonuc['birim_fiyat'])
            y.birim_fiyat = yeni
            y.guncelleme = datetime.now()
            guncellenen += 1
            detaylar.append({
                'id': y.id,
                'baslik': y.baslik,
                'tip': y.tip,
                'eski': round(eski, 4),
                'yeni': round(yeni, 4),
            })
        else:
            atlanan += 1

    db.session.commit()
    return jsonify({
        'ok': True,
        'guncellenen': guncellenen,
        'atlanan': atlanan,
        'detaylar': detaylar,
    })

# ══════════════════════════════════════════════════════════════════════
# API — ALACAKLAR LİSTESİ
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/alacak', methods=['POST'])
def alacak_ekle():
    d = request.json
    a = AlacakListesi(baslik=d['baslik'], url=d.get('url',''),
                      fiyat=float(d['fiyat']) if d.get('fiyat') else None,
                      taksit_sayisi=int(d.get('taksit_sayisi',1)),
                      kategori=d.get('kategori',''), oncelik=d.get('oncelik','orta'),
                      notlar=d.get('notlar',''))
    db.session.add(a); db.session.commit()
    return jsonify({'ok': True, 'id': a.id})

@app.route('/api/alacak/<int:aid>', methods=['PATCH'])
def alacak_guncelle(aid):
    a = AlacakListesi.query.get_or_404(aid)
    d = request.json
    if 'durum' in d: a.durum = d['durum']
    if 'fiyat' in d: a.fiyat = float(d['fiyat'])
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/alacak/<int:aid>', methods=['DELETE'])
def alacak_sil(aid):
    a = AlacakListesi.query.get_or_404(aid)
    db.session.delete(a); db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/alacak/fiyat-cek', methods=['POST'])
def alacak_fiyat_cek():
    if is_privacy_mode_enabled():
        return jsonify({
            'error': 'Gizlilik modu aktif: dış site fiyat çekme kapalı. (PRIVACY_MODE=0 ile açılabilir)'
        }), 403

    url = request.json.get('url','')
    if not url:
        return jsonify({'error': 'URL gerekli'})
    from price_fetcher import fetch_product_info
    return jsonify(fetch_product_info(url))

# ══════════════════════════════════════════════════════════════════════
# API — AI DANIŞMAN
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    soru = request.json.get('soru','').strip()
    if not soru:
        return jsonify({'error': 'Soru boş'})

    pending = AIPendingCommand.query.order_by(AIPendingCommand.id.desc()).first()
    auto_not = None
    cevap = None

    if is_ai_cancel_text(soru):
        if pending:
            db.session.delete(pending)
            db.session.commit()
            cevap = "❎ Bekleyen işlem iptal edildi."
        else:
            cevap = "ℹ️ İptal edilecek bekleyen bir işlem yok."

    elif is_ai_confirm_text(soru):
        if pending:
            try:
                cmd = json.loads(pending.cmd_json)
            except Exception:
                cmd = None

            if cmd:
                auto_not = apply_ai_finance_command(cmd)
                cevap = f"✅ Onay alındı.\n\n{auto_not}"
            else:
                cevap = "⚠️ Bekleyen işlem okunamadı. Lütfen komutu tekrar yaz."

            db.session.delete(pending)
            db.session.commit()
        else:
            cevap = "ℹ️ Onay bekleyen bir işlem yok."

    else:
        cmd = parse_ai_finance_command(soru)
        if cmd:
            # Kullanıcı beklentisi için komutları direkt uygula
            auto_not = apply_ai_finance_command(cmd)
            ay, yil = get_ay_yil()
            ozet = aylik_ozet(ay, yil)
            from ai_advisor import generate_response
            cevap = generate_response(soru, {
                'gelir':        ozet['toplam_gelir'],
                'gider':        ozet['toplam_gider'],
                'sabit_gider':  ozet['toplam_sabit'],
                'taksit':       ozet['toplam_taksit'],
                'kredi':        ozet['toplam_kredi'],
                'gunluk':       ozet['toplam_yol'] + ozet['toplam_yemek'] + ozet['toplam_diger'],
                'yatirim_deger':ozet['toplam_yatirim_deger'],
                'kalan':        ozet['kalan'],
            })
            if auto_not:
                cevap += f"\n\n---\n### 🤖 Otomatik Entegrasyon\n{auto_not}"

    if not cevap:
        ay, yil = get_ay_yil()
        ozet = aylik_ozet(ay, yil)
        from ai_advisor import generate_response
        cevap = generate_response(soru, {
            'gelir':        ozet['toplam_gelir'],
            'gider':        ozet['toplam_gider'],
            'sabit_gider':  ozet['toplam_sabit'],
            'taksit':       ozet['toplam_taksit'],
            'kredi':        ozet['toplam_kredi'],
            'gunluk':       ozet['toplam_yol'] + ozet['toplam_yemek'] + ozet['toplam_diger'],
            'yatirim_deger':ozet['toplam_yatirim_deger'],
            'kalan':        ozet['kalan'],
        })
        if auto_not:
            cevap += f"\n\n---\n### 🤖 Otomatik Entegrasyon\n{auto_not}"

    chat = AIChat(soru=soru, cevap=cevap)
    db.session.add(chat); db.session.commit()
    return jsonify({'ok': True, 'cevap': cevap})

@app.route('/api/ai/analiz')
def ai_analiz():
    ay, yil = get_ay_yil()
    ozet = aylik_ozet(ay, yil)
    from ai_advisor import calculate_health_score
    score, feedback = calculate_health_score({
        'gelir':        ozet['toplam_gelir'],
        'gider':        ozet['toplam_gider'],
        'taksit':       ozet['toplam_taksit'],
        'yatirim_deger':ozet['toplam_yatirim_deger'],
    })
    return jsonify({'score': score, 'feedback': [
        {'icon': f[0], 'text': f[1], 'color': f[2]} for f in feedback
    ]})

@app.route('/api/ai/chat/temizle', methods=['POST'])
def ai_chat_temizle():
    AIChat.query.delete(); db.session.commit()
    AIPendingCommand.query.delete(); db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/ai/gecmis')
def ai_gecmis():
    rows = AIChat.query.order_by(AIChat.tarih.asc()).limit(30).all()
    return jsonify({'ok': True, 'items': [
        {'soru': r.soru, 'cevap': r.cevap, 'tarih': r.tarih.isoformat()} for r in rows
    ]})

# ══════════════════════════════════════════════════════════════════════
# API — PERİYODİK İŞLEMLER
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/periyodik', methods=['POST'])
def periyodik_ekle():
    d = request.json
    p = PeriyodikIslem(
        tur=d.get('tur', 'gider'),
        kategori=d.get('kategori', 'diger'),
        baslik=d['baslik'],
        miktar=float(d['miktar']),
        periyot_ay=int(d.get('periyot_ay', 12)),
        sonraki_tarih=date.fromisoformat(d['sonraki_tarih']),
        notlar=d.get('notlar', '')
    )
    db.session.add(p); db.session.commit()
    return jsonify({'ok': True, 'id': p.id})

@app.route('/api/periyodik/<int:pid>', methods=['PATCH'])
def periyodik_guncelle(pid):
    p = PeriyodikIslem.query.get_or_404(pid)
    d = request.json
    if 'tur' in d: p.tur = d['tur']
    if 'kategori' in d: p.kategori = d['kategori']
    if 'baslik' in d: p.baslik = d['baslik']
    if 'miktar' in d: p.miktar = float(d['miktar'])
    if 'periyot_ay' in d: p.periyot_ay = int(d['periyot_ay'])
    if 'sonraki_tarih' in d: p.sonraki_tarih = date.fromisoformat(d['sonraki_tarih'])
    if 'aktif' in d: p.aktif = bool(d['aktif'])
    if 'notlar' in d: p.notlar = d['notlar']
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/periyodik/<int:pid>/yenile', methods=['POST'])
def periyodik_yenile(pid):
    p = PeriyodikIslem.query.get_or_404(pid)
    p.sonraki_tarih = add_months(p.sonraki_tarih, p.periyot_ay)
    db.session.commit()
    return jsonify({'ok': True, 'sonraki_tarih': p.sonraki_tarih.isoformat()})

@app.route('/api/periyodik/<int:pid>', methods=['DELETE'])
def periyodik_sil(pid):
    p = PeriyodikIslem.query.get_or_404(pid)
    db.session.delete(p); db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/periyodik/hatirlatmalar')
def periyodik_hatirlatmalar():
    days = request.args.get('gun', type=int) or 120
    data = []
    for p in yaklasan_periyodikler(days):
        kalan_gun = (p.sonraki_tarih - date.today()).days
        data.append({
            'id': p.id,
            'tur': p.tur,
            'kategori': p.kategori,
            'baslik': p.baslik,
            'miktar': p.miktar,
            'periyot_ay': p.periyot_ay,
            'sonraki_tarih': p.sonraki_tarih.isoformat(),
            'kalan_gun': kalan_gun,
        })
    return jsonify(data)

# ══════════════════════════════════════════════════════════════════════
# API — GRAFİK VERİLERİ
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/grafik/aylik')
def grafik_aylik():
    sonuc = []
    for m, y in get_last_n_months(6):
        oz = aylik_ozet(m, y)
        sonuc.append({'ay': f"{m}/{y}", 'gelir': oz['toplam_gelir'],
                      'gider': oz['toplam_gider'], 'kalan': oz['kalan']})
    return jsonify(sonuc)

@app.route('/api/grafik/gider-dagilimi')
def grafik_gider():
    ay, yil = get_ay_yil()
    oz = aylik_ozet(ay, yil)
    labels, values, colors = [], [], []
    items = [
        ('Sabit (Kira/Fatura)', oz['toplam_sabit'],   '#e07b39'),
        ('Taksitler',           oz['toplam_taksit'],  '#f87171'),
        ('Kredi Kartı',         oz['toplam_kredi'],   '#fb923c'),
        ('Periyodik',           oz.get('toplam_periyodik_gider', 0), '#c084fc'),
        ('Yol',                 oz['toplam_yol'],     '#facc15'),
        ('Yemek',               oz['toplam_yemek'],   '#4ade80'),
        ('Diğer',               oz['toplam_diger'],   '#94a3b8'),
    ]
    for label, val, color in items:
        if val > 0:
            labels.append(label); values.append(val); colors.append(color)
    return jsonify({'labels': labels, 'values': values, 'colors': colors})

@app.route('/api/grafik/yatirim')
def grafik_yatirim():
    yatirimlar = Yatirim.query.all()
    portfolio = {}
    renk_map = {'dolar':'#22d3ee','euro':'#60a5fa','altin':'#fbbf24',
                'gumus':'#94a3b8','borsa':'#4ade80','kripto':'#f472b6','diger':'#e07b39'}
    for y in yatirimlar:
        tip_label = {'dolar':'USD','euro':'EUR','altin':'Altın','gumus':'Gümüş',
                     'borsa':'Borsa','kripto':'Kripto','diger':'Diğer'}.get(y.tip, y.tip)
        portfolio[tip_label] = portfolio.get(tip_label, {'deger': 0, 'renk': renk_map.get(y.tip,'#e07b39')})
        portfolio[tip_label]['deger'] += y.mevcut_deger
    return jsonify({
        'labels': list(portfolio.keys()),
        'values': [v['deger'] for v in portfolio.values()],
        'colors': [v['renk'] for v in portfolio.values()],
    })

# ══════════════════════════════════════════════════════════════════════
# API — ÖZET
# ══════════════════════════════════════════════════════════════════════

@app.route('/api/ozet')
def ozet_api():
    ay  = request.args.get('ay',  type=int) or get_ay_yil()[0]
    yil = request.args.get('yil', type=int) or get_ay_yil()[1]
    return jsonify(aylik_ozet(ay, yil))

# ══════════════════════════════════════════════════════════════════════
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
