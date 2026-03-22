import os

import price_fetcher


def test_parse_price_basic():
    assert price_fetcher._parse_price('1.234,56 ₺') == 1234.56
    assert price_fetcher._parse_price('2500 TL') == 2500.0


def test_fetch_product_info_privacy_mode_blocks():
    os.environ['PRIVACY_MODE'] = '1'
    data = price_fetcher.fetch_product_info('https://example.com/product')
    assert data['error'] is not None
    assert 'Gizlilik modu' in data['error']
