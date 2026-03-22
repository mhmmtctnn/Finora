import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / 'app'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Test DB'yi izole etmek için import öncesi env ayarı
TEST_DB = ROOT / 'tests' / 'test.db'
os.environ['DB_PATH'] = str(TEST_DB)
os.environ['PRIVACY_MODE'] = '1'

import app as app_module  # noqa: E402


@pytest.fixture()
def client():
    app = app_module.app
    db = app_module.db
    app.config['TESTING'] = True

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as c:
        yield c

    with app.app_context():
        db.session.remove()
        db.drop_all()
