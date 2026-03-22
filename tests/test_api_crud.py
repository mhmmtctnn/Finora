from datetime import date


def test_gelir_crud(client):
    r = client.post('/api/gelir', json={'baslik': 'Maaş', 'miktar': 10000, 'tip': 'maas'})
    assert r.status_code == 200
    gid = r.get_json()['id']

    r = client.delete(f'/api/gelir/{gid}')
    assert r.status_code == 200
    assert r.get_json()['ok'] is True


def test_sabit_gider_post_put_delete(client):
    r = client.post('/api/sabit-gider', json={
        'tip': 'diger', 'baslik': 'Taşınma', 'miktar': 25000, 'aciklama': 'tek seferlik'
    })
    gid = r.get_json()['id']

    r = client.put(f'/api/sabit-gider/{gid}', json={'tip': 'tek_seferlik'})
    assert r.status_code == 200
    assert r.get_json()['tip'] == 'tek_seferlik'

    r = client.delete(f'/api/sabit-gider/{gid}')
    assert r.get_json()['ok'] is True


def test_gunluk_gider_post_put_delete(client):
    r = client.post('/api/gunluk-gider', json={
        'tip': 'diger',
        'baslik': 'Taşıma',
        'miktar': 350,
        'tarih': date.today().isoformat(),
        'aciklama': ''
    })
    gid = r.get_json()['id']

    r = client.put(f'/api/gunluk-gider/{gid}', json={'tip': 'yol'})
    assert r.status_code == 200
    assert r.get_json()['tip'] == 'yol'

    r = client.delete(f'/api/gunluk-gider/{gid}')
    assert r.get_json()['ok'] is True


def test_kredi_karti_post_delete(client):
    r = client.post('/api/kredi-karti', json={'baslik': 'Market', 'miktar': 500, 'kategori': 'market'})
    kid = r.get_json()['id']

    r = client.delete(f'/api/kredi-karti/{kid}')
    assert r.get_json()['ok'] is True


def test_taksit_post_delete(client):
    r = client.post('/api/taksit', json={
        'baslik': 'Telefon',
        'toplam_miktar': 12000,
        'taksit_sayisi': 12,
        'baslangic_ay': 3,
        'baslangic_yil': 2026,
    })
    tid = r.get_json()['id']

    r = client.delete(f'/api/taksit/{tid}')
    assert r.get_json()['ok'] is True


def test_yatirim_post_put_delete(client):
    r = client.post('/api/yatirim', json={
        'tip': 'borsa',
        'sembol': 'THYAO',
        'baslik': 'THYAO',
        'miktar': 10,
        'birim_fiyat': 300,
        'maliyet': 3000,
        'notlar': ''
    })
    yid = r.get_json()['id']

    r = client.put(f'/api/yatirim/{yid}', json={'miktar': 12, 'maliyet': 3600})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok'] is True

    r = client.delete(f'/api/yatirim/{yid}')
    assert r.get_json()['ok'] is True


def test_periyodik_post_patch_delete(client):
    r = client.post('/api/periyodik', json={
        'tur': 'gider',
        'kategori': 'sigorta',
        'baslik': 'Trafik Sigortası',
        'miktar': 5000,
        'periyot_ay': 12,
        'sonraki_tarih': '2026-09-01',
        'notlar': ''
    })
    pid = r.get_json()['id']

    r = client.patch(f'/api/periyodik/{pid}', json={'miktar': 5500})
    assert r.get_json()['ok'] is True

    r = client.delete(f'/api/periyodik/{pid}')
    assert r.get_json()['ok'] is True
