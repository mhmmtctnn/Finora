# price_fetcher.py — URL'den ürün fiyatı ve canlı döviz/altın fiyatı

import os
import re, requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}


def _parse_price(text):
    if not text:
        return None
    text = str(text).strip()
    # Remove currency symbols and whitespace
    clean = re.sub(r'[^\d.,]', '', text)
    if not clean:
        return None
    # Turkish format: 1.234,56 → 1234.56
    if ',' in clean and '.' in clean:
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        # Could be 1234,56 or just 1.234
        parts = clean.split(',')
        if len(parts[1]) <= 2:
            clean = clean.replace(',', '.')
        else:
            clean = clean.replace(',', '')
    try:
        val = float(clean)
        if 0.01 < val < 10_000_000:
            return round(val, 2)
    except Exception:
        pass
    return None


def _get_title(soup):
    for sel in ['h1', '[itemprop="name"]', 'meta[property="og:title"]']:
        el = soup.select_one(sel)
        if el:
            t = el.get('content') or el.get_text(strip=True)
            if t and len(t) > 2:
                return t[:250]
    return None


def _trendyol(soup):
    title, price = None, None
    t = soup.select_one('h1.pr-new-br, h1.product-name, h1[class*="product"]')
    if t:
        title = t.get_text(strip=True)[:250]
    for sel in ['span.prc-dsc', 'span.product-price', '[class*="prc"]', '[class*="price"]']:
        p = soup.select_one(sel)
        if p:
            price = _parse_price(p.get_text())
            if price:
                break
    return title, price


def _hepsiburada(soup):
    title, price = None, None
    t = soup.select_one('h1[id*="product"], h1.product-name, h1[class*="product"]')
    if t:
        title = t.get_text(strip=True)[:250]
    for sel in ['span[id*="currentPrice"]', 'span.price-value',
                '[data-bind*="price"]', '[class*="price"]']:
        p = soup.select_one(sel)
        if p:
            price = _parse_price(p.get_text())
            if price:
                break
    return title, price


def _n11(soup):
    title, price = None, None
    t = soup.select_one('h1.proName, h1.product-name')
    if t:
        title = t.get_text(strip=True)[:250]
    for sel in ['span.newPrice ins', '.currentPrice', '[class*="price"]']:
        p = soup.select_one(sel)
        if p:
            price = _parse_price(p.get_text())
            if price:
                break
    return title, price


def _amazon(soup):
    title, price = None, None
    t = soup.select_one('span#productTitle')
    if t:
        title = t.get_text(strip=True)[:250]
    whole = soup.select_one('span.a-price-whole')
    frac  = soup.select_one('span.a-price-fraction')
    if whole:
        raw = whole.get_text(strip=True)
        if frac:
            raw += '.' + frac.get_text(strip=True)
        price = _parse_price(raw)
    return title, price


def _generic(soup):
    title = _get_title(soup)
    price = None
    # og:price meta tag (most reliable)
    for prop in ['product:price:amount', 'og:price:amount']:
        m = soup.find('meta', property=prop)
        if m and m.get('content'):
            price = _parse_price(m['content'])
            if price:
                break
    if not price:
        # Try schema.org
        el = soup.select_one('[itemprop="price"]')
        if el:
            price = _parse_price(el.get('content') or el.get_text())
    if not price:
        # Last resort: common class names
        for sel in ['[class*="price"]', '[class*="fiyat"]', '[id*="price"]']:
            for el in soup.select(sel):
                val = _parse_price(el.get_text())
                if val:
                    price = val
                    break
            if price:
                break
    return title, price


def fetch_product_info(url: str) -> dict:
    result = {'baslik': None, 'fiyat': None, 'site': None, 'error': None}
    privacy_on = str(os.getenv('PRIVACY_MODE', '1')).strip().lower() in ['1', 'true', 'yes', 'on']
    if privacy_on:
        result['error'] = 'Gizlilik modu aktif: dış site fiyat çekme kapalı.'
        return result

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        url_l = url.lower()
        if 'trendyol.com'    in url_l: t, p = _trendyol(soup)
        elif 'hepsiburada.com' in url_l: t, p = _hepsiburada(soup)
        elif 'n11.com'        in url_l: t, p = _n11(soup)
        elif 'amazon.com.tr'  in url_l: t, p = _amazon(soup)
        else:                           t, p = _generic(soup)

        result['baslik'] = t
        result['fiyat']  = p
        result['site']   = (url_l.split('/')[2].replace('www.', '') if '/' in url_l else url_l)[:50]

    except requests.Timeout:
        result['error'] = 'Bağlantı zaman aşımına uğradı. Lütfen tekrar deneyin.'
    except requests.ConnectionError:
        result['error'] = 'Siteye ulaşılamadı. URL\'yi kontrol edin.'
    except Exception as e:
        result['error'] = f'Hata: {str(e)[:120]}'

    return result


def fetch_live_prices() -> dict:
    """Döviz, altın ve gümüş canlı fiyatları (TRY cinsinden)"""
    data = {}

    # 1. Exchange rates (USD/EUR/GBP → TRY)
    try:
        r = requests.get('https://open.er-api.com/v6/latest/TRY', timeout=6)
        if r.status_code == 200:
            rates = r.json().get('rates', {})
            usd = rates.get('USD')
            eur = rates.get('EUR')
            if usd and usd > 0: data['USD'] = round(1 / usd, 4)
            if eur and eur > 0: data['EUR'] = round(1 / eur, 4)
    except Exception:
        pass

    # 2. Türk finans API (altın, gümüş, döviz)
    try:
        r = requests.get('https://finans.truncgil.com/v4/today.json', timeout=6)
        if r.status_code == 200:
            d = r.json()
            def safe(key, sub='Satış'):
                try:
                    val = d.get(key, {}).get(sub, '')
                    val = str(val).replace(',', '.').replace(' ', '')
                    return round(float(val), 2)
                except Exception:
                    return None

            ga = safe('gram-altin')
            gs = safe('gumus')
            ud = safe('dolar') or safe('USD')
            ed = safe('euro') or safe('EUR')

            if ga: data['GRAM_ALTIN'] = ga
            if gs: data['GUMUS']      = gs
            if ud and 'USD' not in data: data['USD'] = ud
            if ed and 'EUR' not in data: data['EUR'] = ed
    except Exception:
        pass

    data['guncelleme'] = __import__('datetime').datetime.now().strftime('%H:%M:%S')
    return data


def _yahoo_quote(symbol: str):
    """Yahoo quote endpoint: fiyat, para birimi, kısa isim"""
    try:
        url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}'
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None, None, None
        q = r.json().get('quoteResponse', {}).get('result', [])
        if not q:
            return None, None, None
        item = q[0]
        price = item.get('regularMarketPrice')
        curr = item.get('currency')
        name = item.get('shortName') or item.get('longName') or symbol
        if price is None:
            return None, curr, name
        return float(price), curr, name
    except Exception:
        return None, None, None


def _google_finance_bist_quote(symbol: str):
    """Google Finance sayfasından BIST sembolü fiyatını parse et."""
    try:
        s = (symbol or '').upper().replace('.IS', '').replace(':IST', '')
        if not s:
            return None, None, None
        url = f'https://www.google.com/finance/quote/{s}:IST'
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200 or not r.text:
            return None, None, None

        txt = r.text
        # Örnek dizi: ["THYAO","IST"],"Turk Hava Yollari AO",0,"TRY",[289.5,-1.25,...]
        p = re.search(rf'\["{re.escape(s)}","IST"\],"([^"]+)",0,"([A-Z]{{3}})",\[([0-9]+(?:\.[0-9]+)?)', txt)
        if p:
            ad = p.group(1)
            curr = p.group(2)
            price = float(p.group(3))
            return price, curr, ad
    except Exception:
        pass
    return None, None, None


def _crypto_fallback_try_price(symbol: str, usdtry=None):
    """Kripto için Yahoo fallback: önce CoinGecko (TRY), sonra Binance (USDT→TRY)."""
    s = (symbol or '').upper().replace('-USD', '').strip()
    if not s:
        return None, None, None, None

    # 1) CoinGecko: sembol -> id eşlemesi (TRY direkt)
    cg_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'SOL': 'solana',
        'ADA': 'cardano',
        'DOGE': 'dogecoin',
        'AVAX': 'avalanche-2',
        'DOT': 'polkadot',
        'LTC': 'litecoin',
        'LINK': 'chainlink',
        'MATIC': 'matic-network',
        'SHIB': 'shiba-inu',
        'TRX': 'tron',
        'UNI': 'uniswap',
        'ATOM': 'cosmos',
    }
    cg_id = cg_map.get(s)
    if cg_id:
        try:
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=try,usd'
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                j = r.json() or {}
                item = j.get(cg_id) or {}
                p_try = item.get('try')
                p_usd = item.get('usd')
                if p_try:
                    return float(p_try), 'TRY', s, 'coingecko'
                if p_usd and usdtry:
                    return float(p_usd) * float(usdtry), 'TRY', s, 'coingecko-usd'
        except Exception:
            pass

    # 2) Binance: SYMBOLUSDT (USD benzeri), TRY çevir
    try:
        b_symbol = f'{s}USDT'
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={b_symbol}'
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            j = r.json() or {}
            p = j.get('price')
            if p:
                p = float(p)
                if usdtry:
                    return p * float(usdtry), 'TRY', s, 'binance'
                return p, 'USD', s, 'binance'
    except Exception:
        pass

    return None, None, None, None


def fetch_asset_price(tip: str, sembol: str = '') -> dict:
    """
    Tek varlık için anlık birim fiyat getirir (TRY).
    - dolar/euro/altin/gumus: sembol gerekmez
    - borsa: örn THYAO veya THYAO.IS
    - kripto: örn BTC, ETH, BTC-USD
    """
    tip = (tip or '').strip().lower()
    sembol = (sembol or '').strip().upper()

    canli = fetch_live_prices()
    usdtry = canli.get('USD')
    eurtry = canli.get('EUR')

    if tip == 'dolar' and canli.get('USD'):
        return {'ok': True, 'tip': tip, 'sembol': 'USDTRY', 'birim_fiyat': round(float(canli['USD']), 4), 'kaynak': 'truncgil/er-api'}
    if tip == 'euro' and canli.get('EUR'):
        return {'ok': True, 'tip': tip, 'sembol': 'EURTRY', 'birim_fiyat': round(float(canli['EUR']), 4), 'kaynak': 'truncgil/er-api'}
    if tip == 'altin':
        if canli.get('GRAM_ALTIN'):
            return {'ok': True, 'tip': tip, 'sembol': 'GRAM_ALTIN', 'birim_fiyat': round(float(canli['GRAM_ALTIN']), 2), 'kaynak': 'truncgil'}

        # Fallback: gold-api (USD/ons) -> TRY/gram
        try:
            rg = requests.get('https://api.gold-api.com/price/XAU', timeout=7)
            if rg.status_code == 200 and usdtry:
                xau_usd_oz = (rg.json() or {}).get('price')
                if xau_usd_oz:
                    gram_try = (float(xau_usd_oz) * float(usdtry)) / 31.1034768
                    return {'ok': True, 'tip': tip, 'sembol': 'GRAM_ALTIN', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'gold-api'}
        except Exception:
            pass

        # Fallback: ons altın (USD) -> gram TL
        if usdtry:
            xau_usd_oz, _, _ = _yahoo_quote('GC=F')
            if xau_usd_oz:
                gram_try = (float(xau_usd_oz) * float(usdtry)) / 31.1034768
                return {'ok': True, 'tip': tip, 'sembol': 'GRAM_ALTIN', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'yahoo-fallback'}
        # Fallback-2: metal->TRY (ons) -> gram
        try:
            r = requests.get('https://api.exchangerate.host/latest?base=XAU&symbols=TRY', timeout=7)
            if r.status_code == 200:
                xau_try_oz = (r.json().get('rates') or {}).get('TRY')
                if xau_try_oz:
                    gram_try = float(xau_try_oz) / 31.1034768
                    return {'ok': True, 'tip': tip, 'sembol': 'GRAM_ALTIN', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'exchangerate-host'}
        except Exception:
            pass
        # Fallback-3: TCMB XML
        try:
            r = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml', timeout=7)
            if r.status_code == 200 and r.text:
                root = ET.fromstring(r.content)
                for c in root.findall('Currency'):
                    if (c.attrib.get('CurrencyCode') or '').upper() == 'XAU':
                        unit_txt = (c.findtext('Unit') or '1').strip()
                        unit = float(unit_txt) if unit_txt.replace('.', '', 1).isdigit() else 1.0
                        raw = (c.findtext('ForexSelling') or c.findtext('BanknoteSelling') or '').strip()
                        if raw:
                            val = float(raw.replace('.', '').replace(',', '.'))
                            if unit > 0:
                                gram_try = val / unit
                                return {'ok': True, 'tip': tip, 'sembol': 'GRAM_ALTIN', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'tcmb'}
        except Exception:
            pass

    if tip == 'gumus':
        if canli.get('GUMUS'):
            return {'ok': True, 'tip': tip, 'sembol': 'GUMUS', 'birim_fiyat': round(float(canli['GUMUS']), 2), 'kaynak': 'truncgil'}
        # Fallback: ons gümüş (USD) -> gram TL
        if usdtry:
            xag_usd_oz, _, _ = _yahoo_quote('SI=F')
            if xag_usd_oz:
                gram_try = (float(xag_usd_oz) * float(usdtry)) / 31.1034768
                return {'ok': True, 'tip': tip, 'sembol': 'GUMUS', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'yahoo-fallback'}
        # Fallback-2: metal->TRY (ons) -> gram
        try:
            r = requests.get('https://api.exchangerate.host/latest?base=XAG&symbols=TRY', timeout=7)
            if r.status_code == 200:
                xag_try_oz = (r.json().get('rates') or {}).get('TRY')
                if xag_try_oz:
                    gram_try = float(xag_try_oz) / 31.1034768
                    return {'ok': True, 'tip': tip, 'sembol': 'GUMUS', 'birim_fiyat': round(float(gram_try), 2), 'kaynak': 'exchangerate-host'}
        except Exception:
            pass

    if tip == 'borsa':
        if not sembol:
            return {'ok': False, 'error': 'Borsa için sembol gerekli (örn: THYAO).'}
        yahoo_symbol = sembol if '.' in sembol else f'{sembol}.IS'
        price, curr, name = _yahoo_quote(yahoo_symbol)
        if price is None:
            # Yahoo kota/erişim sorunu olursa Google Finance fallback
            g_price, g_curr, g_name = _google_finance_bist_quote(sembol)
            if g_price is not None:
                price, curr, name = g_price, g_curr, g_name
                yahoo_symbol = f'{sembol}:IST'
            else:
                return {'ok': False, 'error': f'Sembol bulunamadı: {yahoo_symbol}'}

        if curr == 'TRY' or not curr:
            try_price = price
        elif curr == 'USD' and usdtry:
            try_price = price * float(usdtry)
        elif curr == 'EUR' and eurtry:
            try_price = price * float(eurtry)
        else:
            return {'ok': False, 'error': f'{curr} → TRY dönüşümü yapılamadı.'}

        return {
            'ok': True,
            'tip': tip,
            'sembol': yahoo_symbol,
            'ad': name,
            'birim_fiyat': round(float(try_price), 4),
            'kaynak': 'yahoo-finance'
        }

    if tip == 'kripto':
        if not sembol:
            sembol = 'BTC'
        yahoo_symbol = sembol if '-' in sembol else f'{sembol}-USD'
        price, curr, name = _yahoo_quote(yahoo_symbol)
        if price is None:
            fb_price, fb_curr, fb_name, fb_source = _crypto_fallback_try_price(sembol, usdtry=usdtry)
            if fb_price is None:
                return {'ok': False, 'error': f'Kripto sembolü bulunamadı: {yahoo_symbol}'}
            return {
                'ok': True,
                'tip': tip,
                'sembol': yahoo_symbol,
                'ad': fb_name or sembol,
                'birim_fiyat': round(float(fb_price), 4),
                'kaynak': fb_source or 'fallback'
            }

        if curr == 'USD' and usdtry:
            try_price = price * float(usdtry)
        elif curr == 'TRY' or not curr:
            try_price = price
        else:
            return {'ok': False, 'error': f'{curr} → TRY dönüşümü yapılamadı.'}

        return {
            'ok': True,
            'tip': tip,
            'sembol': yahoo_symbol,
            'ad': name,
            'birim_fiyat': round(float(try_price), 4),
            'kaynak': 'yahoo-finance'
        }

    return {'ok': False, 'error': 'Bu tür için canlı fiyat desteği yok.'}
