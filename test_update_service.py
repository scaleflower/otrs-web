"""Auto-update service integration smoke test"""

import sys
import os

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import init_db, AppUpdateStatus
from services import init_services, update_service
import services.update_service as update_module


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = 'ok'

    def json(self):
        return self._payload


def test_update_service_check():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['APP_UPDATE_ENABLED'] = False  # avoid network call during init

    init_db(app)
    init_services(app)

    with app.app_context():
        status = AppUpdateStatus.query.first()
        assert status is not None
        assert status.current_version == app.config.get('APP_VERSION', '0.0.0')

    # Patch requests.get to return fake release
    original_get = update_module.requests.get

    def fake_get(url, headers=None, timeout=10):
        return _FakeResponse(payload={
            'tag_name': 'v9.9.9',
            'name': 'Release 9.9.9',
            'body': 'Bug fixes',
            'html_url': 'https://example.com/release',
            'published_at': '2024-01-01T00:00:00Z'
        })

    update_module.requests.get = fake_get

    try:
        app.config['APP_UPDATE_ENABLED'] = True
        update_service.initialize(app)
        result = update_service.check_for_updates(force=True)
        assert result['latest_version'] == 'v9.9.9'
        status = update_service.get_status()
        assert status['latest_version'] == 'v9.9.9'
        assert status['status'] == 'update_available'
    finally:
        update_module.requests.get = original_get
