import pytest
from fastapi.testclient import TestClient

from app.clock import FixedClock
from app.main import create_app
from tests.helpers import FIXED_NOW, make_settings


@pytest.fixture
def clock():
    return FixedClock(FIXED_NOW)


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture
def app(settings, clock):
    return create_app(settings, clock=clock)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def services(app):
    return app.state.services
