import importlib

from fastapi.testclient import TestClient


def test_admin_auth_required(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")

    from api import settings

    importlib.reload(settings)
    from api import app as app_module

    importlib.reload(app_module)

    client = TestClient(app_module.app)
    response = client.get("/api/admin/metrics")
    assert response.status_code == 401
