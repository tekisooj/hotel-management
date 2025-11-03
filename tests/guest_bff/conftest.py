import os
import json
import pytest
import anyio
from fastapi.testclient import TestClient

from bffs.guest_bff.app.main import app  # type: ignore


@pytest.fixture
def bff_env(monkeypatch):
    monkeypatch.setenv("GUEST_BFF_ENV", "test")
    monkeypatch.setenv("AUDIENCE", "test-aud")
    monkeypatch.setenv("JWKS_URL", "https://example.com/.well-known/jwks.json")
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test-client")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    yield


@pytest.fixture
def bff_client(bff_env):
    return TestClient(app)
