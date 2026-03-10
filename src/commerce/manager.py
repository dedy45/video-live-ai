"""Layer 7: Commerce — Product Management & Script Engine.

Manages product catalog, rotation, selling scripts, and affiliate tracking.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.data.database import get_connection
from src.utils.logging import get_logger

logger = get_logger("commerce")


@dataclass
class Product:
    """Product data model."""

    id: int = 0
    name: str = ""
    price: float = 0.0
    image_path: str = ""
    description: str = ""
    stock: int = 0
    category: str = "general"
    margin_percent: float = 0.0
    is_active: bool = True
    features: list[str] = field(default_factory=list)

    # Affiliate fields
    affiliate_links: dict[str, str] = field(default_factory=dict)  # platform -> link
    selling_points: list[str] = field(default_factory=list)
    commission_rate: float = 0.0  # percentage
    objection_handling: dict[str, str] = field(default_factory=dict)  # objection -> response
    compliance_notes: str = ""

    @property
    def price_formatted(self) -> str:
        return f"Rp {self.price:,.0f}"


@dataclass
class SellingScript:
    """7-phase selling script for a product."""

    product_id: int
    phases: dict[str, str] = field(default_factory=dict)
    total_duration_sec: int = 30
    generated_at: float = 0.0

    @property
    def hook(self) -> str:
        return self.phases.get("hook", "")

    @property
    def cta(self) -> str:
        return self.phases.get("cta", "")


class ProductManager:
    """Product catalog management with rotation scheduling.

    Requirements: 7.1-7.4 — CRUD, search, categorization.
    """

    CANONICAL_PRODUCTS_PATH = Path("data/products.json")

    def __init__(self) -> None:
        self._products: list[Product] = []
        self._current_index = 0
        self._rotation_interval_sec = 240  # 4 minutes
        self._last_rotation = time.time()

        logger.info("product_manager_init")

    def load_from_json(self, path: Path | None = None) -> int:
        """Load products from a JSON file. Returns count of products loaded."""
        source = path or self.CANONICAL_PRODUCTS_PATH
        if not source.exists():
            logger.warning("product_json_not_found", path=str(source))
            return 0
        try:
            import json
            data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                logger.warning("product_json_invalid", path=str(source), reason="not a list")
                return 0
            count = 0
            for item in data:
                product = Product(
                    name=item.get("name", ""),
                    price=float(item.get("price", 0)),
                    description=item.get("description", ""),
                    category=item.get("category", "general"),
                    stock=int(item.get("stock", 0)),
                    image_path=item.get("image", ""),
                    features=item.get("selling_points", []),
                    is_active=True,
                )
                self.add_product(product)
                count += 1
            logger.info("products_loaded_from_json", path=str(source), count=count)
            return count
        except Exception as e:
            logger.error("product_json_load_error", path=str(source), error=str(e))
            return 0

    def add_product(self, product: Product) -> Product:
        """Add product to catalog."""
        product.id = len(self._products) + 1
        self._products.append(product)
        logger.info("product_added", name=product.name, id=product.id)
        return product

    def get_current_product(self) -> Product | None:
        """Get currently displayed product."""
        if not self._products:
            return None
        return self._products[self._current_index % len(self._products)]

    def rotate_next(self) -> Product | None:
        """Rotate to next product."""
        if not self._products:
            return None
        self._current_index = (self._current_index + 1) % len(self._products)
        self._last_rotation = time.time()
        product = self._products[self._current_index]
        logger.info("product_rotated", name=product.name, index=self._current_index)
        return product

    def should_rotate(self) -> bool:
        """Check if it's time to rotate products."""
        return (time.time() - self._last_rotation) >= self._rotation_interval_sec

    def get_all_active(self) -> list[Product]:
        """Get all active products."""
        return [p for p in self._products if p.is_active]

    def search(self, query: str) -> list[Product]:
        """Search products by name or category."""
        q = query.lower()
        return [
            p for p in self._products
            if q in p.name.lower() or q in p.category.lower()
        ]


class ScriptEngine:
    """Selling script generation and caching.

    Requirements: 7.5 — 7-phase selling script (Hook→CTA).
    Uses LLM Brain for generation, caches results.
    """

    def __init__(self) -> None:
        self._cache: dict[int, SellingScript] = {}
        self._cache_ttl = 24 * 3600  # 24 hours

    def get_cached_script(self, product_id: int) -> SellingScript | None:
        """Get cached script if still valid."""
        script = self._cache.get(product_id)
        if script and (time.time() - script.generated_at) < self._cache_ttl:
            return script
        return None

    def cache_script(self, script: SellingScript) -> None:
        """Cache a generated script."""
        script.generated_at = time.time()
        self._cache[script.product_id] = script
        logger.info("script_cached", product_id=script.product_id)

    def parse_script_response(self, product_id: int, llm_text: str) -> SellingScript:
        """Parse LLM response into structured 7-phase script."""
        phases: dict[str, str] = {}
        phase_names = ["hook", "problem", "solution", "features", "social_proof", "urgency", "cta"]

        lines = llm_text.strip().split("\n")
        current_phase = ""
        current_text: list[str] = []

        for line in lines:
            line_lower = line.lower().strip()
            matched = False
            for phase in phase_names:
                if phase in line_lower and (":" in line or "." in line):
                    if current_phase and current_text:
                        phases[current_phase] = " ".join(current_text).strip()
                    current_phase = phase
                    current_text = []
                    # Extract text after the label
                    parts = line.split(":", 1) if ":" in line else line.split(".", 1)
                    if len(parts) > 1 and parts[1].strip():
                        current_text.append(parts[1].strip())
                    matched = True
                    break
            if not matched and current_phase:
                current_text.append(line.strip())

        if current_phase and current_text:
            phases[current_phase] = " ".join(current_text).strip()

        return SellingScript(product_id=product_id, phases=phases)


@dataclass
class AffiliateEvent:
    """Affiliate tracking event."""

    platform: str
    product_id: int
    event_type: str  # click, add_to_cart, purchase
    estimated_commission: float = 0.0
    currency: str = "IDR"


class AffiliateTracker:
    """Tracks affiliate commissions and conversions.

    Requirements: 8.1-8.4 — TikTok Affiliate & Shopee Affiliate tracking.
    """

    def __init__(self) -> None:
        self._events: list[AffiliateEvent] = []
        self._total_commission = 0.0

    def track_event(self, event: AffiliateEvent) -> None:
        """Record an affiliate event."""
        self._events.append(event)
        self._total_commission += event.estimated_commission
        logger.info(
            "affiliate_event",
            platform=event.platform,
            type=event.event_type,
            commission=event.estimated_commission,
        )

    def get_daily_summary(self) -> dict[str, Any]:
        """Get daily affiliate summary."""
        clicks = sum(1 for e in self._events if e.event_type == "click")
        carts = sum(1 for e in self._events if e.event_type == "add_to_cart")
        purchases = sum(1 for e in self._events if e.event_type == "purchase")
        return {
            "clicks": clicks,
            "add_to_cart": carts,
            "purchases": purchases,
            "total_commission": self._total_commission,
            "conversion_rate": purchases / max(clicks, 1),
        }
