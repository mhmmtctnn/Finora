import ai_advisor


def test_health_score_with_no_income():
    score, feedback = ai_advisor.calculate_health_score({'gelir': 0})
    assert score == 40
    assert feedback


def test_ai_chat_budget_analysis(client):
    client.post('/api/gelir', json={'baslik': 'Maaş', 'miktar': 20000, 'tip': 'maas'})
    r = client.post('/api/ai/chat', json={'soru': 'bütçe analizi'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok'] is True
    assert 'Bütçe Analizi' in data['cevap'] or 'Genel Finansal Özet' in data['cevap']


def test_ai_chat_auto_add_expense(client):
    r = client.post('/api/ai/chat', json={'soru': '460 tl telefon faturası ekle'})
    assert r.status_code == 200
    data = r.get_json()
    assert data['ok'] is True
    assert 'eklendi' in data['cevap'].lower()
