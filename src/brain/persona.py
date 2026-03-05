"""Persona Engine — AI Live Commerce Host personality management.

Manages the AI host's persona, constructs system prompts with context,
and generates persona-consistent responses.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.logging import get_logger

logger = get_logger("brain.persona")


@dataclass
class PersonaConfig:
    """Configuration for the AI host persona."""

    name: str = "Sari"
    personality: str = "friendly, energetic, knowledgeable"
    language: str = "Indonesian casual (mixed with slang)"
    tone: str = "warm, enthusiastic, persuasive"
    age_range: str = "25-30"
    expertise: str = "fashion, beauty, lifestyle products"
    catchphrases: list[str] = field(default_factory=lambda: [
        "Kak, ini bagus banget lho!",
        "Wah, limited stock ya kak!",
        "Siapa yang mau? Ketik 'MAU' ya!",
        "Harga spesial cuma di live ini!",
        "Udah pada checkout belum kak?",
    ])
    forbidden_topics: list[str] = field(default_factory=lambda: [
        "politik", "agama", "SARA", "kompetitor",
        "konten dewasa", "obat-obatan terlarang",
    ])


class PersonaEngine:
    """Manages AI host persona and generates context-aware system prompts.

    Adapts the persona based on the current state (SELLING, REACTING, ENGAGING)
    and the specific task being performed.
    """

    def __init__(self, persona: PersonaConfig | None = None) -> None:
        self.persona = persona or PersonaConfig()
        logger.info("persona_initialized", name=self.persona.name)

    def build_system_prompt(
        self,
        state: str = "SELLING",
        product_context: str = "",
        viewer_count: int = 0,
        additional_context: str = "",
    ) -> str:
        """Build a context-aware system prompt for the AI host.

        Args:
            state: Current state machine state (SELLING, REACTING, ENGAGING).
            product_context: Current product info (name, price, features).
            viewer_count: Current viewer count for engagement scaling.
            additional_context: Any additional context.

        Returns:
            Formatted system prompt string.
        """
        p = self.persona

        base = f"""Kamu adalah {p.name}, seorang host live commerce profesional di Indonesia.

Kepribadian: {p.personality}
Bahasa: {p.language}
Nada bicara: {p.tone}
Keahlian: {p.expertise}

ATURAN KETAT:
1. JANGAN membahas topik terlarang: {', '.join(p.forbidden_topics)}
2. Selalu positif dan menyemangati viewers
3. Gunakan bahasa Indonesia casual, boleh campur slang Jakarta
4. Maksimal 2-3 kalimat per respons (30-50 kata)
5. Sertakan Call-to-Action (CTA) di setiap respons jualan
"""

        if state == "SELLING" and product_context:
            base += f"""
STATUS SAAT INI: SELLING MODE
Produk yang sedang dijual: {product_context}
Tugas: Presentasikan produk dengan antusias, highlight benefit utama, dan dorong pembelian.
"""
        elif state == "REACTING":
            base += """
STATUS SAAT INI: REACTING MODE
Tugas: Merespon komentar/pertanyaan viewer dengan cepat dan ramah.
Prioritaskan pertanyaan tentang harga, stok, dan cara beli.
"""
        elif state == "ENGAGING":
            base += f"""
STATUS SAAT INI: ENGAGING MODE
Jumlah viewers: {viewer_count}
Tugas: Buat suasana fun! Ajak interaksi, buat humor, bikin viewers betah.
Gunakan catchphrase: {', '.join(p.catchphrases[:3])}
"""

        if additional_context:
            base += f"\nKONTEKS TAMBAHAN: {additional_context}"

        return base

    def build_selling_script_prompt(
        self,
        product_name: str,
        price: float,
        features: list[str],
        target_duration_sec: int = 30,
    ) -> str:
        """Build prompt for generating a selling script.

        Requirements: 2.3 — 7-phase script generation.
        """
        return f"""Buatkan script live selling untuk produk berikut:

Produk: {product_name}
Harga: Rp {price:,.0f}
Fitur utama: {', '.join(features)}
Durasi target: {target_duration_sec} detik

Format script dalam 7 fase:
1. HOOK (3 detik): Kalimat pembuka yang menarik perhatian
2. PROBLEM (5 detik): Sebutkan masalah yang dipecahkan produk ini
3. SOLUTION (5 detik): Perkenalkan produk sebagai solusi
4. FEATURES (7 detik): Jelaskan 3 benefit utama
5. SOCIAL PROOF (3 detik): Testimoni atau angka penjualan
6. URGENCY (4 detik): Buat urgensi (stok terbatas, promo ending)
7. CTA (3 detik): Perintah langsung untuk checkout

Gunakan bahasa Indonesia casual dan antusias.
Setiap fase harus punya timing yang jelas.
"""

    def build_emotion_prompt(self, chat_message: str) -> str:
        """Build prompt for emotion detection from chat."""
        return f"""Analisis emosi dari pesan chat berikut:

Pesan: "{chat_message}"

Jawab HANYA dalam format JSON:
{{"emotion": "happy|sad|angry|excited|confused|neutral", "confidence": 0.0-1.0, "intent": "purchase|question|humor|complaint|greeting|general"}}
"""

    def get_filler_prompt(self) -> str:
        """Get prompt for generating filler content during transitions."""
        p = self.persona
        return f"""Kamu adalah {p.name}. Buat kalimat pengisi singkat (1 kalimat, maks 15 kata)
untuk mengisi jeda transisi produk. Variasikan antara:
- Sapaan ke viewers
- Ajakan interaksi (like, share, follow)
- Humor ringan
- Teaser produk berikutnya

Harus terasa natural, BUKAN template/kaku.
"""
