"""Versioned prompt registry for persona and script templates."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.data.database import DB_PATH

DEFAULT_PERSONA = {
    "name": "Sari",
    "personality": "friendly, energetic, knowledgeable",
    "language": "Indonesian casual (mixed with slang)",
    "tone": "warm, enthusiastic, persuasive",
    "expertise": "fashion, beauty, lifestyle products",
    "catchphrases": [
        "Kak, ini bagus banget lho!",
        "Wah, limited stock ya kak!",
        "Siapa yang mau? Ketik 'MAU' ya!",
        "Harga spesial cuma di live ini!",
        "Udah pada checkout belum kak?",
    ],
    "forbidden_topics": [
        "politik",
        "agama",
        "SARA",
        "kompetitor",
        "konten dewasa",
        "obat-obatan terlarang",
    ],
}

DEFAULT_TEMPLATES = {
    "system_base": (
        "Kamu adalah {name}, seorang host live commerce profesional di Indonesia.\n\n"
        "Kepribadian: {personality}\n"
        "Bahasa: {language}\n"
        "Nada bicara: {tone}\n"
        "Keahlian: {expertise}\n\n"
        "ATURAN KETAT:\n"
        "1. JANGAN membahas topik terlarang: {forbidden_topics}\n"
        "2. Selalu positif dan menyemangati viewers\n"
        "3. Gunakan bahasa Indonesia casual, boleh campur slang Jakarta\n"
        "4. Maksimal 2-3 kalimat per respons (30-50 kata)\n"
        "5. Sertakan Call-to-Action (CTA) di setiap respons jualan"
    ),
    "selling_mode": (
        "STATUS SAAT INI: SELLING MODE\n"
        "Produk yang sedang dijual: {product_context}\n"
        "Tugas: Presentasikan produk dengan antusias, highlight benefit utama, dan dorong pembelian."
    ),
    "reacting_mode": (
        "STATUS SAAT INI: REACTING MODE\n"
        "Tugas: Merespon komentar/pertanyaan viewer dengan cepat dan ramah.\n"
        "Prioritaskan pertanyaan tentang harga, stok, dan cara beli."
    ),
    "engaging_mode": (
        "STATUS SAAT INI: ENGAGING MODE\n"
        "Jumlah viewers: {viewer_count}\n"
        "Tugas: Buat suasana fun! Ajak interaksi, buat humor, bikin viewers betah.\n"
        "Gunakan catchphrase: {catchphrases}"
    ),
    "filler": (
        "Kamu adalah {name}. Buat kalimat pengisi singkat (1 kalimat, maks 15 kata)\n"
        "untuk mengisi jeda transisi produk. Variasikan antara:\n"
        "- Sapaan ke viewers\n"
        "- Ajakan interaksi (like, share, follow)\n"
        "- Humor ringan\n"
        "- Teaser produk berikutnya\n\n"
        "Harus terasa natural, BUKAN template/kaku."
    ),
    "selling_script": (
        "Buatkan script live selling untuk produk berikut:\n\n"
        "Produk: {product_name}\n"
        "Harga: Rp {price:,.0f}\n"
        "Fitur utama: {features}\n"
        "Durasi target: {target_duration_sec} detik\n\n"
        "Format script dalam 7 fase:\n"
        "1. HOOK (3 detik): Kalimat pembuka yang menarik perhatian\n"
        "2. PROBLEM (5 detik): Sebutkan masalah yang dipecahkan produk ini\n"
        "3. SOLUTION (5 detik): Perkenalkan produk sebagai solusi\n"
        "4. FEATURES (7 detik): Jelaskan 3 benefit utama\n"
        "5. SOCIAL PROOF (3 detik): Testimoni atau angka penjualan\n"
        "6. URGENCY (4 detik): Buat urgensi (stok terbatas, promo ending)\n"
        "7. CTA (3 detik): Perintah langsung untuk checkout\n\n"
        "Gunakan bahasa Indonesia casual dan antusias.\n"
        "Setiap fase harus punya timing yang jelas.\n"
        "Tulis eksplisit bahwa ini terdiri dari 7 fase."
    ),
}


class PromptRegistry:
    """SQLite-backed prompt registry with a default active revision."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._bootstrap_default()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    templates_json TEXT NOT NULL,
                    persona_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(slug, version)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_revisions_slug_status ON prompt_revisions(slug, status)"
            )

    def _bootstrap_default(self) -> None:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM prompt_revisions WHERE status = 'active' ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if existing is not None:
                return
            conn.execute(
                """
                INSERT INTO prompt_revisions (slug, version, status, templates_json, persona_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "default-live-commerce",
                    1,
                    "active",
                    json.dumps(DEFAULT_TEMPLATES, ensure_ascii=True),
                    json.dumps(DEFAULT_PERSONA, ensure_ascii=True),
                ),
            )

    def get_active_revision(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, slug, version, status, templates_json, persona_json, created_at, updated_at
                FROM prompt_revisions
                WHERE status = 'active'
                ORDER BY version DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("No active prompt revision found")
        return {
            "id": row["id"],
            "slug": row["slug"],
            "version": row["version"],
            "status": row["status"],
            "templates": json.loads(row["templates_json"]),
            "persona": json.loads(row["persona_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


_prompt_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = PromptRegistry()
    return _prompt_registry
