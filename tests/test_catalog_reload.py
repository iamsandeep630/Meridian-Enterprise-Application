"""
Tests for Catalog Sync and Protected Admin Reload Endpoint
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app
from database import SessionLocal, Product, init_db
from database.catalog_sync import apply_catalog_config
from config import ADMIN_SYNC_KEY

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_reload_missing_auth():
    """Verify endpoint rejects requests without X-Sync-Key with 401."""
    res = client.post("/api/admin/catalog/reload", json={})
    assert res.status_code == 401
    assert "Unauthorized" in res.json().get("detail", "")

def test_reload_invalid_auth():
    """Verify endpoint rejects requests with invalid X-Sync-Key with 401."""
    res = client.post(
        "/api/admin/catalog/reload",
        json={},
        headers={"X-Sync-Key": "incorrect-secret-key"}
    )
    assert res.status_code == 401

def test_reload_invalid_json():
    """Verify endpoint rejects invalid JSON content with 400."""
    res = client.post(
        "/api/admin/catalog/reload",
        json={"content": "not-valid-json-string{}"},
        headers={"X-Sync-Key": ADMIN_SYNC_KEY}
    )
    assert res.status_code == 400
    assert "Invalid JSON content" in res.json().get("detail", "")

def test_reload_success_and_products_updated():
    """Verify reload applies show_in_invoice_dropdown=True and GET /products reflects it."""
    # 1. Update to True
    payload = {
        "content": {
            "products": {
                "4K Webcam Pro": {
                    "show_in_invoice_dropdown": True
                }
            }
        }
    }
    res = client.post(
        "/api/admin/catalog/reload",
        json=payload,
        headers={"X-Sync-Key": ADMIN_SYNC_KEY}
    )
    assert res.status_code == 200
    assert res.json().get("success") is True

    # 2. Check GET /products
    p_res = client.get("/products")
    assert p_res.status_code == 200
    prods = p_res.json()
    webcam = next((p for p in prods if p["name"] == "4K Webcam Pro"), None)
    assert webcam is not None
    assert webcam["show_in_invoice_dropdown"] == 1

    # 3. Reset back to False
    reset_payload = {
        "content": {
            "products": {
                "4K Webcam Pro": {
                    "show_in_invoice_dropdown": False
                }
            }
        }
    }
    res_reset = client.post(
        "/api/admin/catalog/reload",
        json=reset_payload,
        headers={"X-Sync-Key": ADMIN_SYNC_KEY}
    )
    assert res_reset.status_code == 200

    # 4. Verify reset
    p_res2 = client.get("/products")
    prods2 = p_res2.json()
    webcam2 = next((p for p in prods2 if p["name"] == "4K Webcam Pro"), None)
    assert webcam2 is not None
    assert webcam2["show_in_invoice_dropdown"] == 0

def test_catalog_sync_resilience_to_invalid_file(tmp_path):
    """Verify apply_catalog_config handles corrupt JSON without crashing."""
    bad_file = tmp_path / "bad_catalog.json"
    bad_file.write_text("{{corrupted-json}}")

    db = SessionLocal()
    try:
        res = apply_catalog_config(db, config_path=bad_file)
        assert res["status"] == "warning"
        assert res["reason"] == "invalid_json"
    finally:
        db.close()
