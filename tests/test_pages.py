def test_all_main_pages_load(client):
    pages = [
        '/',
        '/gelirler',
        '/sabit-giderler',
        '/taksitler',
        '/kredi-karti',
        '/gunluk-giderler',
        '/yatirimlar',
        '/alacaklar',
        '/periyodikler',
        '/ai-danisma',
    ]

    for p in pages:
        r = client.get(p)
        assert r.status_code == 200, f'page failed: {p}'
