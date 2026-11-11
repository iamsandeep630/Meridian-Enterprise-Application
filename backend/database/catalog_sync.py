"""
Catalog Synchronization Module
Applies product configuration from catalog_config.json to database.
"""
import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Product

logger = logging.getLogger("catalog_sync")

CONFIG_PATH = Path(__file__).resolve().parent.parent / "catalog_config.json"

def apply_catalog_config(db: Session, config_path: Path | str | None = None) -> dict:
    """
    Applies product settings (like show_in_invoice_dropdown) from catalog_config.json.
    Gracefully ignores invalid JSON or missing files with a warning.
    """
    target_path = Path(config_path) if config_path else CONFIG_PATH
    if not target_path.exists():
        logger.warning(f"[CatalogSync] Config file not found at: {target_path}")
        return {"status": "skipped", "reason": "file_not_found"}

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"[CatalogSync] Invalid JSON in {target_path}: {e}")
        return {"status": "warning", "reason": "invalid_json", "error": str(e)}
    except Exception as e:
        logger.warning(f"[CatalogSync] Error reading {target_path}: {e}")
        return {"status": "warning", "reason": "read_error", "error": str(e)}

    if not isinstance(data, dict):
        logger.warning(f"[CatalogSync] Top-level config must be a JSON object: {target_path}")
        return {"status": "warning", "reason": "invalid_format"}

    products_config = data.get("products", {})
    if not isinstance(products_config, dict):
        logger.warning("[CatalogSync] 'products' key must be an object")
        return {"status": "warning", "reason": "invalid_products_format"}

    updated = []
    for prod_name, settings in products_config.items():
        if not isinstance(settings, dict):
            continue

        prod = db.query(Product).filter(Product.name == prod_name).first()
        if prod:
            if "show_in_invoice_dropdown" in settings:
                val = settings["show_in_invoice_dropdown"]
                # Convert bool or int to 1/0
                prod.show_in_invoice_dropdown = 1 if val is True or val == 1 else 0
                updated.append({"name": prod.name, "show_in_invoice_dropdown": prod.show_in_invoice_dropdown})

    try:
        db.commit()
        logger.info(f"[CatalogSync] Successfully applied config for {len(updated)} products.")
        return {"status": "success", "updated": updated}
    except Exception as e:
        db.rollback()
        logger.error(f"[CatalogSync] Failed to commit catalog updates: {e}")
        return {"status": "error", "error": str(e)}
