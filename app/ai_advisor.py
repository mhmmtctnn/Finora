# ai_advisor.py — Kural tabanlı Türkçe Finansal Danışman

def calculate_health_score(data):
    income  = data.get('gelir', 0)
    gider   = data.get('gider', 0)
    taksit  = data.get('taksit', 0)
    yatirim = data.get('yatirim_deger', 0)
    feedback = []
    score = 100

    if income == 0:
        return 40, [('⚠️', 'Gelir bilgisi girilmemiş', 'orange')]

    exp_ratio = gider / income
    if exp_ratio < 0.50:
        feedback.append(('✅', f'Mükemmel gider kontrolü (Gelirinizin %{exp_ratio*100:.0f}\'i)', 'green'))
    elif exp_ratio < 0.70:
        score -= 10
        feedback.append(('📊', f'Giderler gelirinizin %{exp_ratio*100:.0f}\'i — iyileştirme payı var', 'yellow'))
    elif exp_ratio < 0.90:
        score -= 25
        feedback.append(('⚠️', f'Yüksek gider oranı! (Gelirinizin %{exp_ratio*100:.0f}\'i)', 'orange'))
    else:
        score -= 45
        feedback.append(('🚨', 'Giderler gelirinizi aşıyor — acil önlem gerekli!', 'red'))

    tak_ratio = taksit / income
    if tak_ratio < 0.20:
        feedback.append(('✅', f'Taksit yükü makul (%{tak_ratio*100:.0f})', 'green'))
    elif tak_ratio < 0.35:
        score -= 15
        feedback.append(('⚠️', f'Taksit yükü biraz yüksek (%{tak_ratio*100:.0f})', 'orange'))
    else:
        score -= 30
        feedback.append(('🚨', f'Taksit yükü kritik (%{tak_ratio*100:.0f}) — yeni alım yapmayın!', 'red'))

    yat_ratio = yatirim / income
    if yat_ratio >= 6:
        feedback.append(('📈', '6 aylık gelir kadar yatırım portföyü — harika!', 'green'))
    elif yat_ratio >= 2:
        score -= 5
        feedback.append(('📊', 'Yatırım portföyü büyüyor', 'blue'))
    else:
        score -= 15
        feedback.append(('💡', 'Yatırım portföyünüzü büyütmeye odaklanın', 'yellow'))

    return max(0, min(100, score)), feedback


def get_intent(q):
    q = q.lower()
    if any(w in q for w in ['merhaba', 'selam', 'nasılsın', 'kimsin', 'nedir']):
        return 'greeting'
    if any(w in q for w in ['tasarruf', 'biriktir', 'para biriktir', 'birikim']):
        return 'savings'
    if any(w in q for w in ['yatırım', 'hisse', 'borsa', 'dolar', 'altın', 'euro', 'kripto', 'gümüş', 'portföy']):
        return 'investment'
    if any(w in q for w in ['bütçe', 'harcama', 'gider', 'masraf', 'plan']):
        return 'budget'
    if any(w in q for w in ['borç', 'kredi', 'taksit', 'faiz', 'ödeme']):
        return 'debt'
    if any(w in q for w in ['acil', 'fon', 'beklenmedik', 'güvenlik', 'yastık']):
        return 'emergency'
    if any(w in q for w in ['emekli', 'emeklilik', 'yaşlılık']):
        return 'retirement'
    if any(w in q for w in ['skor', 'puan', 'durum', 'değerlendir', 'rapor', 'sağlık']):
        return 'health'
    if any(w in q for w in ['al', 'satın', 'alacak', 'ürün', 'liste']):
        return 'shopping'
    return 'general'


def generate_response(question, fd):
    intent  = get_intent(question)
    income  = fd.get('gelir', 0)
    gider   = fd.get('gider', 0)
    sabit   = fd.get('sabit_gider', 0)
    taksit  = fd.get('taksit', 0)
    kredi   = fd.get('kredi', 0)
    gunluk  = fd.get('gunluk', 0)
    yatirim = fd.get('yatirim_deger', 0)
    kalan   = fd.get('kalan', income - gider)
    score, feedback = calculate_health_score(fd)

    if intent == 'greeting':
        return f"""## 👋 Merhaba! Ben BütçePlan AI Danışmanınızım

Finansal durumunuza hızlı bir bakış:

| Kategori | Tutar |
|----------|-------|
| 💵 Aylık Gelir | {income:,.2f} ₺ |
| 💸 Toplam Gider | {gider:,.2f} ₺ |
| 💰 Net Kalan | {kalan:+,.2f} ₺ |
| 📈 Yatırım Portföyü | {yatirim:,.2f} ₺ |
| 🏥 Finansal Sağlık Skoru | **{score}/100** |

Size şu konularda yardımcı olabilirim:
- 💰 **"tasarruf stratejisi"** → Kişisel tasarruf planı
- 📈 **"yatırım tavsiyesi"** → Portföy önerileri
- 📊 **"bütçe analizi"** → Harcama optimizasyonu
- 💳 **"taksit yönetimi"** → Borç planlaması
- 🛡️ **"acil fon"** → Güvenlik ağı oluşturma
- 🏖️ **"emeklilik planı"** → Uzun vadeli strateji
- 🏥 **"finansal sağlık"** → Detaylı skor raporu

Ne öğrenmek istersiniz?"""

    if intent == 'savings':
        save_rate = (kalan / income * 100) if income > 0 else 0
        opt_save  = income * 0.20
        return f"""## 💰 Tasarruf Analizi

**Mevcut Durumunuz:**
- Aylık Gelir: **{income:,.2f} ₺**
- Toplam Gider: **{gider:,.2f} ₺**
- Net Tasarruf: **{max(0, kalan):,.2f} ₺** (Gelirinizin %{max(0,save_rate):.1f}'i)

**Önerilen 50/30/20 Kuralı:**
| Kategori | Oran | Sizin için |
|----------|------|------------|
| 🏠 İhtiyaçlar (Kira, faturalar) | %50 | {income * 0.50:,.0f} ₺ |
| 🎯 İstekler (Eğlence, alışveriş) | %30 | {income * 0.30:,.0f} ₺ |
| 💰 Tasarruf & Yatırım | %20 | {income * 0.20:,.0f} ₺ |

{"⚠️ **Uyarı:** Tasarruf oranınız çok düşük. Sabit giderlerinizi gözden geçirin." if save_rate < 10 else "✅ **Harika!** %20+ tasarruf oranı finansal özgürlüğün temelidir!" if save_rate >= 20 else "📊 Tasarruf oranınızı artırmak için küçük adımlar atın."}

**5 Hızlı Tasarruf Taktiği:**
1. Her ay ilk günü **{opt_save:,.0f} ₺** otomatik olarak ayrı hesaba aktar
2. Büyük alımlar için **48 saat bekleme kuralı** uygula
3. Aylık aboneliklerini gözden geçir (streaming, üyelikler)
4. Haftalık yemek planı yaparak market harcamalarını azalt
5. Nakit ödeme yap — kredi kartı harcamayı kolaylaştırır"""

    if intent == 'investment':
        return f"""## 📈 Yatırım Tavsiyeleri — 2026

**Portföy Durumunuz:** {yatirim:,.2f} ₺
**Aylık Yatırım Kapasitesi:** {max(0, kalan):,.2f} ₺

**Türkiye için Önerilen Portföy Dağılımı:**
| Varlık | Oran | Neden? |
|--------|------|--------|
| 🥇 Gram Altın | %25–30 | TL değer kaybına en güçlü koruma |
| 💵 USD / 💶 EUR | %20–25 | Döviz riski hedge'i |
| 📈 BIST Hisse Senedi | %20–25 | Uzun vadede yüksek büyüme |
| 🏦 TL Mevduat / DİBS | %15–20 | Likidite + faiz geliri |
| ₿ Kripto (isteğe bağlı) | %5–10 | Yüksek risk / yüksek potansiyel |

**⚡ Pratik Yatırım Tüyoları:**
- Altın alımı için **gram altın** dövizden daha pratiktir
- Hisse senedi için **en az 3–5 yıllık** vade düşünün
- **DCA (düzenli alım)** ile piyasa zamanlamasından kaçının
- Kripto için kaybetmeye razı olduğunuz parayı kullanın

**Aylık {max(0,kalan):,.0f} ₺ ile önerilen dağılım:**
- Altın: {max(0,kalan)*0.30:,.0f} ₺
- Döviz: {max(0,kalan)*0.25:,.0f} ₺
- Borsa: {max(0,kalan)*0.25:,.0f} ₺
- Mevduat: {max(0,kalan)*0.20:,.0f} ₺"""

    if intent == 'budget':
        if income == 0:
            return "Bütçe analizi için önce gelir bilgilerinizi girmeniz gerekiyor. Sol menüden **Gelirler** sayfasına gidin."
        exp_ratio = gider / income
        return f"""## 📊 Bütçe Analizi — {datetime.now().strftime('%B %Y') if True else ''}

**Aylık Tablo:**
| Kategori | Tutar | Gelir Oranı |
|----------|-------|-------------|
| 💵 Gelir | {income:,.2f} ₺ | %100 |
| 🏠 Sabit Giderler | {sabit:,.2f} ₺ | %{sabit/income*100:.1f} |
| 📆 Taksitler | {taksit:,.2f} ₺ | %{taksit/income*100:.1f} |
| 💳 Kredi Kartı | {kredi:,.2f} ₺ | %{kredi/income*100:.1f} |
| 🚗 Günlük Giderler | {gunluk:,.2f} ₺ | %{gunluk/income*100:.1f} |
| **💰 Net Kalan** | **{kalan:+,.2f} ₺** | **%{kalan/income*100:.1f}** |

{"🚨 **KRİTİK:** Giderler gelirinizi aşıyor! 1) Taksit almayı durdurun 2) Sabit giderleri düşürün 3) Ek gelir arayın" if exp_ratio >= 0.90 else "⚠️ **Dikkat:** Gider oranı %70+ seviyesinde. Azaltılabilir harcamaları kısmayı deneyin." if exp_ratio >= 0.70 else "✅ Bütçeniz sağlıklı görünüyor! Kalan parayı yatırıma yönlendirin."}

**Azaltılabilecek Alanlar:**
1. Dışarıda yemek sıklığını haftada 2'ye indirin → tahmini tasarruf: ₺{gunluk*0.2:,.0f}/ay
2. Aboneliklerinizi kontrol edin (Netflix, Spotify, gym üyelikleri)
3. Toplu taşıma vs özel araç maliyetini karşılaştırın"""

    if intent == 'debt':
        tak_ratio = taksit / income if income > 0 else 0
        borc_orani = ((taksit + kredi) / income * 100) if income > 0 else 0
        return f"""## 💳 Borç & Taksit Yönetimi

**Borç Durumu:**
- Aylık Taksit: **{taksit:,.2f} ₺** (Gelirinizin %{tak_ratio*100:.1f}'i)
- Kredi Kartı: **{kredi:,.2f} ₺**
- Toplam Borç Yükü: **{(taksit+kredi):,.2f} ₺** (Gelirinizin %{borc_orani:.1f}'i)

**Değerlendirme:** {"🚨 Borç yükü kritik seviyede — yeni taksit/kredi ALMAYIN!" if tak_ratio > 0.35 else "⚠️ Borç yükü yüksek — mevcut taksitler bitene kadar bekleyin." if tak_ratio > 0.20 else "✅ Borç yükü makul seviyede."}

**Borç Azaltma Stratejileri:**

🔥 **Çığ Yöntemi** (en ucuz uzun vadede):
En yüksek faizli borcu önce öde

⛄ **Kartopu Yöntemi** (en motive edici):
En küçük bakiyeyi önce kapat, motivasyonu koru

**Altın Kurallar:**
- Kredi kartı borcunu **hiçbir zaman minimum ödeyle** bırakma
- Nakit avans kullanma (aylık %4-5 faiz)
- Yeni taksit almadan önce mevcut taksitlerini bitir
- Taksit yükünü gelirinizin **%30'unun altında** tut"""

    if intent == 'emergency':
        hedef3 = gider * 3
        hedef6 = gider * 6
        return f"""## 🛡️ Acil Fon Planlaması

**Neden Acil Fon?**
İş kaybı, sağlık problemi, araç arızası gibi beklenmedik durumlarda borçlanmadan hayatını sürdürmeni sağlar.

**Senin İçin Hedefler:**
| Seçenek | Tutar | Aylık {max(1,kalan):,.0f} ₺ ile süre |
|---------|-------|------|
| 🟡 Minimum (3 ay) | {hedef3:,.2f} ₺ | {hedef3/max(1,kalan):.1f} ay |
| ✅ Önerilen (6 ay) | {hedef6:,.2f} ₺ | {hedef6/max(1,kalan):.1f} ay |

**Acil Fon Nerede Tutulmalı?**
1. 🏦 **Yüksek faizli vadesiz hesap** (en likit, anında erişim)
2. 📋 **1 aylık vadeli mevduat** (biraz daha faiz)
3. 🥇 **Gram altın** (enflasyona karşı)

**⚠️ Dikkat:** Acil fon yatırım değildir. Hisse senedi veya kripto olmamalı — değer kaybı riskini taşıyamazsın."""

    if intent == 'retirement':
        hedef = gider * 12 * 25
        return f"""## 🏖️ Emeklilik Planlaması

**Emeklilikte ne kadar gerekli?**
Finansal bağımsızlık için popüler formül: **Yıllık gider × 25**

Eğer emeklilikte aylık {gider:,.0f} ₺ harcarsanız:
→ **Hedef Portföy: {hedef:,.0f} ₺**

**Mevcut Durum:**
- Portföyünüz: {yatirim:,.0f} ₺
- Hedefe kalan: {max(0, hedef - yatirim):,.0f} ₺
- Aylık yatırım kapasitesi: {max(0,kalan):,.0f} ₺

**Önerilen Emeklilik Portföy Dağılımı:**
| Varlık | Oran | Gerekçe |
|--------|------|---------|
| 📈 Hisse ETF | %40–60 | Uzun vadeli büyüme motoru |
| 🏦 Tahvil / DİBS | %20–30 | İstikrar, faiz geliri |
| 🥇 Altın | %15–20 | Enflasyon koruması |
| 💵 Döviz | %10–15 | Kur riski hedge'i |

**BES Avantajları:**
- Devlet katkısı: **%30** (bedava para!)
- Vergi avantajı
- Uzun vadeli birikim disiplini"""

    if intent == 'health':
        bar = '🟩' * (score // 10) + '⬜' * (10 - score // 10)
        return f"""## 🏥 Finansal Sağlık Raporu

**Skorunuz: {score}/100**
{bar}

**Durum:** {'🟢 MÜKEMMEL' if score >= 80 else '🟡 İYİ' if score >= 60 else '🟠 ORTA' if score >= 40 else '🔴 ZAYIF'}

**Değerlendirme:**
{"".join(f"- {f[0]} {f[1]}{chr(10)}" for f in feedback)}
**Özet Tablo:**
| | |
|-|-|
| 💵 Gelir | {income:,.2f} ₺ |
| 💸 Gider | {gider:,.2f} ₺ |
| 💰 Kalan | {kalan:+,.2f} ₺ |
| 📈 Yatırım | {yatirim:,.2f} ₺ |

**Skoru Yükseltmek İçin:**
{"- Tasarruf oranını %20'ye çıkar" + chr(10) if kalan < income * 0.20 else ""}{"- Taksit yükünü azalt" + chr(10) if taksit > income * 0.25 else ""}{"- Yatırım portföyü oluştur / büyüt" + chr(10) if yatirim < income * 3 else ""}- Acil fon oluştur (3–6 aylık gider)"""

    if intent == 'shopping':
        return f"""## 🛍️ Alışveriş & Satın Alma Tavsiyeleri

**Bütçe Durumunuz:**
- Aylık kullanılabilir para: **{max(0,kalan):,.2f} ₺**
- Yatırım için ayrılması gereken: **{max(0,kalan)*0.5:,.2f} ₺**
- Alışveriş için kalan: **{max(0,kalan)*0.3:,.2f} ₺**

**Satın Alma Kurallarım:**
1. **Fiyatı {max(0,kalan)*0.5:,.0f} ₺ altı** → Hemen alınabilir
2. **Fiyatı {max(0,kalan)*0.5:,.0f}–{max(0,kalan)*2:,.0f} ₺ arası** → 1 ay bekle, fiyat düşer mi ara
3. **Fiyatı {max(0,kalan)*2:,.0f} ₺ üstü** → Bütçe planı yap, taksiti incele

**Akıllı Alışveriş Taktikleri:**
- Alacaklar listesini kullan (sol menü) — URL ekle, otomatik fiyat çeksin
- Trendyol/Hepsiburada kampanya dönemlerini takip et (11.11, yılbaşı)
- Kredi kartı taksitini bütçenin %30'unu geçmesin
- İhtiyaç mı, istek mi? — 48 saat bekle"""

    # General
    return f"""## 💡 Genel Finansal Özet

**Bu Ay Durumunuz:**
| | |
|-|-|
| 💵 Gelir | {income:,.2f} ₺ |
| 💸 Gider | {gider:,.2f} ₺ |
| 💰 Net Kalan | {kalan:+,.2f} ₺ |
| 📈 Yatırım Portföyü | {yatirim:,.2f} ₺ |
| 🏥 Sağlık Skoru | {score}/100 |

**Önerilen Konular:**
Aşağıdakilerden birini yazın:
- _"tasarruf stratejisi"_ → Kişisel tasarruf planı
- _"yatırım tavsiyesi"_ → 2026 portföy önerileri
- _"bütçe analizi"_ → Harcama dağılımı
- _"finansal sağlık"_ → Detaylı skor raporu
- _"taksit yönetimi"_ → Borç durumu analizi
- _"acil fon"_ → Güvenlik ağı planı
- _"emeklilik planı"_ → Uzun vade stratejisi"""


# avoid circular import for datetime
from datetime import datetime
