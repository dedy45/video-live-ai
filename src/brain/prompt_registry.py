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
    "role": "affiliate_host",
    "platform": "tiktok_live",
    "market": "indonesia",
    "audience_style": "national_casual",
    "product_relationship": "recommender_not_owner",
    "knowledge_boundaries": [
        "cannot_confirm_stock",
        "cannot_confirm_shipping_final",
        "cannot_claim_medical_results",
        "cannot_offer_store_guarantee",
    ],
    "viewer_address_terms": [
        "kak",
        "bestie",
        "guys",
    ],
    "soft_cta_patterns": [
        "cek linknya ya kak",
        "lihat dulu di keranjang kuning",
        "kalau cocok baru checkout",
    ],
    "unknown_answer_policy": "redirect_to_product_page",
    "experience_mode": "grounded_only",
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
        "Role: {role}\n"
        "Platform: {platform}\n"
        "Market: {market}\n"
        "Relasi dengan produk: {product_relationship}\n"
        "Sapaan penonton: {viewer_address_terms}\n"
        "Soft CTA: {soft_cta_patterns}\n"
        "Unknown answer policy: {unknown_answer_policy}\n"
        "Batas pengetahuan: {knowledge_boundaries}\n"
        "Experience mode: {experience_mode}\n\n"
        "ATURAN KETAT:\n"
        "1. JANGAN membahas topik terlarang: {forbidden_topics}\n"
        "2. Selalu positif dan menyemangati viewers\n"
        "3. Gunakan bahasa Indonesia casual nasional, jangan terdengar seperti robot\n"
        "4. Jangan mengaku sebagai brand owner atau pemilik toko\n"
        "5. Jika data tidak ada, jawab jujur lalu arahkan ke halaman produk\n"
        "6. CTA harus natural, bukan wajib di setiap respons"
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
    "chat_reply": (
        "Viewer bernama {viewer_name} berkata: {viewer_message}\n"
        "Produk saat ini: {product_context}\n"
        "Konteks tambahan: {additional_context}\n\n"
        "Jawab dalam 1-3 kalimat spoken Indonesian yang natural.\n"
        "Jawab inti pertanyaan dulu. CTA hanya jika relevan.\n"
        "Kalau data tidak tersedia, jawab jujur lalu arahkan ke halaman produk.\n"
        "Jangan terdengar seperti chatbot atau brand owner."
    ),
    "product_qa": (
        "Pertanyaan produk: {question}\n"
        "Konteks produk: {product_context}\n"
        "Konteks tambahan: {additional_context}\n\n"
        "Jawab secara faktual, ringkas, dan konservatif.\n"
        "Jangan mengarang bahan, stok, garansi, hasil medis, atau pengiriman final."
    ),
    "emotion_detect": (
        "Analisis recent chats berikut:\n{recent_chats}\n\n"
        "Jawab HANYA JSON dengan field: state, intent_summary, priority, recommended_action, confidence."
    ),
    "humor": (
        "Buat 1-2 kalimat humor ringan yang aman, relevan dengan live commerce,\n"
        "dan tidak menghina siapapun."
    ),
    "safety_check": (
        "Periksa candidate text berikut:\n{candidate_text}\n"
        "Konteks produk: {product_context}\n"
        "Konteks tambahan: {additional_context}\n\n"
        "Jawab HANYA JSON dengan field: safe, reason_code, blocked_phrases, rewrite, operator_review_required."
    ),
    "fallback_unknown_answer": (
        "Wah yang itu aku nggak mau asal jawab ya kak, coba cek detail lengkapnya di halaman produk."
    ),
    "fallback_policy_blocked": (
        "Untuk bagian itu aku jawab sesuai info resmi yang tersedia aja ya kak."
    ),
    "fallback_operator_handoff": (
        "Sebentar ya kak, ini lebih aman dicek operator dulu biar infonya nggak keliru."
    ),
}


class PromptRegistry:
    """SQLite-backed prompt registry with a default active revision."""

    REQUIRED_TEMPLATE_KEYS = {
        "system_base",
        "selling_mode",
        "reacting_mode",
        "engaging_mode",
        "filler",
        "selling_script",
    }
    REQUIRED_PERSONA_KEYS = {
        "name",
        "personality",
        "language",
        "tone",
        "expertise",
        "catchphrases",
        "forbidden_topics",
    }
    OPTIONAL_SCALAR_PERSONA_KEYS = {
        "role",
        "platform",
        "market",
        "audience_style",
        "product_relationship",
        "unknown_answer_policy",
        "experience_mode",
    }
    OPTIONAL_LIST_PERSONA_KEYS = {
        "knowledge_boundaries",
        "viewer_address_terms",
        "soft_cta_patterns",
    }

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
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_single_active
                ON prompt_revisions(status)
                WHERE status = 'active'
                """
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

    def _serialize_row(self, row: sqlite3.Row) -> dict[str, Any]:
        templates_payload = json.loads(row["templates_json"])
        persona_payload = json.loads(row["persona_json"])
        templates = dict(DEFAULT_TEMPLATES)
        templates.update(templates_payload)
        persona = dict(DEFAULT_PERSONA)
        persona.update(persona_payload)
        return {
            "id": row["id"],
            "slug": row["slug"],
            "version": row["version"],
            "status": row["status"],
            "templates": templates,
            "persona": persona,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _validate_templates(self, templates: dict[str, Any]) -> None:
        missing = sorted(self.REQUIRED_TEMPLATE_KEYS.difference(templates.keys()))
        if missing:
            raise ValueError(f"Missing required template keys: {', '.join(missing)}")

        for key in self.REQUIRED_TEMPLATE_KEYS:
            value = templates.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Template '{key}' must be a non-empty string")

        for key, value in templates.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Template '{key}' must be a non-empty string")

    def _validate_persona(self, persona: dict[str, Any]) -> None:
        missing = sorted(self.REQUIRED_PERSONA_KEYS.difference(persona.keys()))
        if missing:
            raise ValueError(f"Missing required persona keys: {', '.join(missing)}")

        scalar_keys = ["name", "personality", "language", "tone", "expertise"]
        for key in scalar_keys:
            value = persona.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Persona field '{key}' must be a non-empty string")

        for key in ("catchphrases", "forbidden_topics"):
            value = persona.get(key)
            if not isinstance(value, list) or not value:
                raise ValueError(f"Persona field '{key}' must be a non-empty list")
            if not all(isinstance(item, str) and item.strip() for item in value):
                raise ValueError(f"Persona field '{key}' must contain non-empty strings")

        for key in self.OPTIONAL_SCALAR_PERSONA_KEYS:
            if key not in persona:
                continue
            value = persona.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Persona field '{key}' must be a non-empty string")

        for key in self.OPTIONAL_LIST_PERSONA_KEYS:
            if key not in persona:
                continue
            value = persona.get(key)
            if not isinstance(value, list) or not value:
                raise ValueError(f"Persona field '{key}' must be a non-empty list")
            if not all(isinstance(item, str) and item.strip() for item in value):
                raise ValueError(f"Persona field '{key}' must contain non-empty strings")

    def validate_payload(self, *, templates: dict[str, Any], persona: dict[str, Any]) -> None:
        self._validate_templates(templates)
        self._validate_persona(persona)

    def list_revisions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, slug, version, status, templates_json, persona_json, created_at, updated_at
                FROM prompt_revisions
                ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
        return [self._serialize_row(row) for row in rows]

    def get_revision(self, revision_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, slug, version, status, templates_json, persona_json, created_at, updated_at
                FROM prompt_revisions
                WHERE id = ?
                """,
                (revision_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Prompt revision {revision_id} not found")
        return self._serialize_row(row)

    def create_revision(
        self,
        *,
        slug: str,
        templates: dict[str, Any],
        persona: dict[str, Any],
    ) -> dict[str, Any]:
        slug_value = slug.strip()
        if not slug_value:
            raise ValueError("Slug must be a non-empty string")
        self.validate_payload(templates=templates, persona=persona)

        with self._connect() as conn:
            max_version = conn.execute(
                "SELECT MAX(version) AS max_v FROM prompt_revisions WHERE slug = ?",
                (slug_value,),
            ).fetchone()
            next_version = (max_version["max_v"] or 0) + 1
            cursor = conn.execute(
                """
                INSERT INTO prompt_revisions (slug, version, status, templates_json, persona_json)
                VALUES (?, ?, 'draft', ?, ?)
                """,
                (
                    slug_value,
                    next_version,
                    json.dumps(templates, ensure_ascii=False),
                    json.dumps(persona, ensure_ascii=False),
                ),
            )
            new_id = int(cursor.lastrowid)
        return self.get_revision(new_id)

    def update_revision(
        self,
        revision_id: int,
        *,
        templates: dict[str, Any],
        persona: dict[str, Any],
    ) -> dict[str, Any]:
        self.validate_payload(templates=templates, persona=persona)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM prompt_revisions WHERE id = ?",
                (revision_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Prompt revision {revision_id} not found")
            if row["status"] != "draft":
                raise ValueError(f"Cannot edit {row['status']} revision (only drafts can be edited)")

            conn.execute(
                """
                UPDATE prompt_revisions
                SET templates_json = ?, persona_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    json.dumps(templates, ensure_ascii=False),
                    json.dumps(persona, ensure_ascii=False),
                    revision_id,
                ),
            )
        return self.get_revision(revision_id)

    def publish_revision(self, revision_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM prompt_revisions WHERE id = ?",
                (revision_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Prompt revision {revision_id} not found")
            if row["status"] != "draft":
                raise ValueError(f"Cannot publish {row['status']} revision (only drafts can be published)")

            conn.execute(
                "UPDATE prompt_revisions SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE status = 'active'"
            )
            conn.execute(
                """
                UPDATE prompt_revisions
                SET status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (revision_id,),
            )
        return self.get_revision(revision_id)

    def delete_revision(self, revision_id: int) -> dict[str, Any]:
        revision = self.get_revision(revision_id)
        if revision["status"] != "draft":
            raise ValueError(f"Cannot delete {revision['status']} revision (only drafts can be deleted)")

        with self._connect() as conn:
            conn.execute("DELETE FROM prompt_revisions WHERE id = ?", (revision_id,))
        return {"id": revision_id, "status": "deleted"}

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
        return self._serialize_row(row)


_prompt_registry: PromptRegistry | None = None


def get_prompt_registry() -> PromptRegistry:
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = PromptRegistry()
    return _prompt_registry
