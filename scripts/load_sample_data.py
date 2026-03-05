"""Load Sample Data Script.

Requirements: 13.8 — Populates the catalog by reading `sample_products.json`
and writes the loaded count out.
"""
import json
import logging
from pathlib import Path

# Ensure project root on sys path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.commerce.manager import Product, ProductManager

logger = logging.getLogger("load_sample_data")
logging.basicConfig(level=logging.INFO)

def main() -> None:
    path = Path(__file__).parent.parent / "data" / "sample_products.json"
    if not path.exists():
        logger.error(f"Sample data file not found: {path}")
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pm = ProductManager()
        for item in data:
            product = Product(
                name=item["name"],
                price=float(item["price"]),
                description=item["description"],
                stock=item["stock"],
                category=item["category"],
                features=item.get("selling_points", []),
            )
            pm.add_product(product)
        logger.info(f"Successfully loaded {len(data)} products.")
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
