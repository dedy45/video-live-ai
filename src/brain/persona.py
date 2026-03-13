"""Persona Engine — AI Live Commerce Host personality management.

Manages the AI host's persona, constructs system prompts with context,
and generates persona-consistent responses.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES, get_prompt_registry
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
    role: str = "affiliate_host"
    platform: str = "tiktok_live"
    market: str = "indonesia"
    audience_style: str = "national_casual"
    product_relationship: str = "recommender_not_owner"
    knowledge_boundaries: list[str] = field(default_factory=lambda: [
        "cannot_confirm_stock",
        "cannot_confirm_shipping_final",
        "cannot_claim_medical_results",
        "cannot_offer_store_guarantee",
    ])
    viewer_address_terms: list[str] = field(default_factory=lambda: [
        "kak",
        "bestie",
        "guys",
    ])
    soft_cta_patterns: list[str] = field(default_factory=lambda: [
        "cek linknya ya kak",
        "lihat dulu di keranjang kuning",
        "kalau cocok baru checkout",
    ])
    unknown_answer_policy: str = "redirect_to_product_page"
    experience_mode: str = "grounded_only"
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
            payload = {**DEFAULT_PERSONA, **revision["persona"]}
            self.persona = PersonaConfig(
                name=payload.get("name", "Sari"),
                personality=payload.get("personality", "friendly, energetic, knowledgeable"),
                language=payload.get("language", "Indonesian casual (mixed with slang)"),
                tone=payload.get("tone", "warm, enthusiastic, persuasive"),
                expertise=payload.get("expertise", "fashion, beauty, lifestyle products"),
                role=payload.get("role", "affiliate_host"),
                platform=payload.get("platform", "tiktok_live"),
                market=payload.get("market", "indonesia"),
                audience_style=payload.get("audience_style", "national_casual"),
                product_relationship=payload.get("product_relationship", "recommender_not_owner"),
                knowledge_boundaries=list(payload.get("knowledge_boundaries", [])),
                viewer_address_terms=list(payload.get("viewer_address_terms", [])),
                soft_cta_patterns=list(payload.get("soft_cta_patterns", [])),
                unknown_answer_policy=payload.get("unknown_answer_policy", "redirect_to_product_page"),
                experience_mode=payload.get("experience_mode", "grounded_only"),
                catchphrases=list(payload.get("catchphrases", [])),
                forbidden_topics=list(payload.get("forbidden_topics", [])),
            )
        logger.info("persona_initialized", name=self.persona.name)

    def _get_templates(self) -> dict[str, str]:
        revision = get_prompt_registry().get_active_revision()
        return {**DEFAULT_TEMPLATES, **dict(revision["templates"])}

    def _template_context(self) -> dict[str, str]:
        p = self.persona
        return {
            "name": p.name,
            "personality": p.personality,
            "language": p.language,
            "tone": p.tone,
            "expertise": p.expertise,
            "forbidden_topics": ", ".join(p.forbidden_topics),
            "catchphrases": ", ".join(p.catchphrases[:3]),
            "role": p.role,
            "platform": p.platform,
            "market": p.market,
            "audience_style": p.audience_style,
            "product_relationship": p.product_relationship,
            "knowledge_boundaries": ", ".join(p.knowledge_boundaries),
            "viewer_address_terms": ", ".join(p.viewer_address_terms),
            "soft_cta_patterns": ", ".join(p.soft_cta_patterns),
            "unknown_answer_policy": p.unknown_answer_policy,
            "experience_mode": p.experience_mode,
        }

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
        templates = self._get_templates()
        context = self._template_context()

        base = templates["system_base"].format(
            **context,
        )

        if state == "SELLING" and product_context:
            base += "\n\n" + templates["selling_mode"].format(product_context=product_context)
        elif state == "REACTING":
            base += "\n\n" + templates["reacting_mode"]
        elif state == "ENGAGING":
            base += "\n\n" + templates["engaging_mode"].format(
                viewer_count=viewer_count,
                catchphrases=context["catchphrases"],
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

    def build_chat_reply_prompt(
        self,
        *,
        viewer_name: str,
        viewer_message: str,
        product_context: str = "",
        additional_context: str = "",
    ) -> str:
        """Build prompt for viewer chat replies."""
        return self._get_templates()["chat_reply"].format(
            viewer_name=viewer_name.strip() or "viewer",
            viewer_message=viewer_message.strip(),
            product_context=product_context.strip() or "Tidak ada produk fokus",
            additional_context=additional_context.strip() or "-",
        )

    def build_product_qa_prompt(
        self,
        *,
        question: str,
        product_context: str,
        additional_context: str = "",
    ) -> str:
        """Build prompt for fact-bound product Q&A."""
        return self._get_templates()["product_qa"].format(
            question=question.strip(),
            product_context=product_context.strip(),
            additional_context=additional_context.strip() or "-",
        )

    def build_safety_check_prompt(
        self,
        *,
        candidate_text: str,
        product_context: str,
        additional_context: str = "",
    ) -> str:
        """Build prompt for pre-output safety filtering."""
        return self._get_templates()["safety_check"].format(
            candidate_text=candidate_text.strip(),
            product_context=product_context.strip(),
            additional_context=additional_context.strip() or "-",
        )

    def build_emotion_prompt(self, chat_message: str | list[str]) -> str:
        """Build prompt for emotion detection from recent chat context."""
        if isinstance(chat_message, list):
            recent_chats = "\n".join(f"- {message}" for message in chat_message)
        else:
            recent_chats = chat_message
        return self._get_templates()["emotion_detect"].format(recent_chats=recent_chats.strip())

    def get_filler_prompt(self) -> str:
        """Get prompt for generating filler content during transitions."""
        return self._get_templates()["filler"].format(name=self.persona.name)
