"""
Tests for Catalog Sync and Protected Admin Reload Endpoint
"""
import unittest
import json
import tempfile
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


class TestCatalogReload(unittest.TestCase):

    def setUp(self):
        init_db()
        self.client = TestClient(app)

    def test_reload_missing_auth(self):
        """Verify endpoint rejects requests without X-Sync-Key with 401."""
        res = self.client.post("/api/admin/catalog/reload", json={})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Unauthorized", res.json().get("detail", ""))

    def test_reload_invalid_auth(self):
        """Verify endpoint rejects requests with invalid X-Sync-Key with 401."""
        res = self.client.post(
            "/api/admin/catalog/reload",
            json={},
            headers={"X-Sync-Key": "incorrect-secret-key"}
        )
        self.assertEqual(res.status_code, 401)

    def test_reload_invalid_json(self):
        """Verify endpoint rejects invalid JSON content with 400."""
        res = self.client.post(
            "/api/admin/catalog/reload",
            json={"content": "not-valid-json-string{}"},
            headers={"X-Sync-Key": ADMIN_SYNC_KEY}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid JSON content", res.json().get("detail", ""))

    def test_reload_success_and_products_updated(self):
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
        res = self.client.post(
            "/api/admin/catalog/reload",
            json=payload,
            headers={"X-Sync-Key": ADMIN_SYNC_KEY}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

        # 2. Check GET /products
        p_res = self.client.get("/products")
        self.assertEqual(p_res.status_code, 200)
        prods = p_res.json()
        webcam = next((p for p in prods if p["name"] == "4K Webcam Pro"), None)
        self.assertIsNotNone(webcam)
        self.assertEqual(webcam["show_in_invoice_dropdown"], 1)

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
        res_reset = self.client.post(
            "/api/admin/catalog/reload",
            json=reset_payload,
            headers={"X-Sync-Key": ADMIN_SYNC_KEY}
        )
        self.assertEqual(res_reset.status_code, 200)

        # 4. Verify reset
        p_res2 = self.client.get("/products")
        self.assertEqual(p_res2.status_code, 200)
        prods2 = p_res2.json()
        webcam2 = next((p for p in prods2 if p["name"] == "4K Webcam Pro"), None)
        self.assertIsNotNone(webcam2)
        self.assertEqual(webcam2["show_in_invoice_dropdown"], 0)

    def test_catalog_sync_resilience_to_invalid_file(self):
        """Verify apply_catalog_config handles corrupt JSON without crashing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_file = Path(tmp_dir) / "bad_catalog.json"
            bad_file.write_text("{{corrupted-json}}", encoding="utf-8")

            db = SessionLocal()
            try:
                res = apply_catalog_config(db, config_path=bad_file)
                self.assertEqual(res["status"], "warning")
                self.assertEqual(res["reason"], "invalid_json")
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
