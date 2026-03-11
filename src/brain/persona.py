"""Persona Engine — AI Live Commerce Host personality management.

Manages the AI host's persona, constructs system prompts with context,
and generates persona-consistent responses.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.brain.prompt_registry import get_prompt_registry
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
        if persona is not None:
            self.persona = persona
        else:
            revision = get_prompt_registry().get_active_revision()
            payload = revision["persona"]
            self.persona = PersonaConfig(
                name=payload.get("name", "Sari"),
                personality=payload.get("personality", "friendly, energetic, knowledgeable"),
                language=payload.get("language", "Indonesian casual (mixed with slang)"),
                tone=payload.get("tone", "warm, enthusiastic, persuasive"),
                expertise=payload.get("expertise", "fashion, beauty, lifestyle products"),
                catchphrases=list(payload.get("catchphrases", [])),
                forbidden_topics=list(payload.get("forbidden_topics", [])),
            )
        logger.info("persona_initialized", name=self.persona.name)

    def _get_templates(self) -> dict[str, str]:
        revision = get_prompt_registry().get_active_revision()
        return dict(revision["templates"])

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
        templates = self._get_templates()

        base = templates["system_base"].format(
            name=p.name,
            personality=p.personality,
            language=p.language,
            tone=p.tone,
            expertise=p.expertise,
            forbidden_topics=", ".join(p.forbidden_topics),
        )

        if state == "SELLING" and product_context:
            base += "\n\n" + templates["selling_mode"].format(product_context=product_context)
        elif state == "REACTING":
            base += "\n\n" + templates["reacting_mode"]
        elif state == "ENGAGING":
            base += "\n\n" + templates["engaging_mode"].format(
                viewer_count=viewer_count,
                catchphrases=", ".join(p.catchphrases[:3]),
            )

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
        return self._get_templates()["selling_script"].format(
            product_name=product_name,
            price=price,
            features=", ".join(features),
            target_duration_sec=target_duration_sec,
        )

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
        return self._get_templates()["filler"].format(name=p.name)
