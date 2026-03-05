"""Content Safety Filter — Input/Output Guardrails.

Filters LLM output before sending to TTS to prevent inappropriate content.
Requirements: 32.1, 32.2, 32.3, 32.4
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from src.utils.logging import get_logger

logger = get_logger("brain.safety")

# Keyword blacklist — Indonesian + English banned terms
BLACKLIST_KEYWORDS: list[str] = [
    # SARA
    "suku", "ras", "agama", "kafir", "sesat",
    # Vulgar
    "anjing", "bangsat", "babi", "kontol", "memek",
    # Drugs
    "narkoba", "ganja", "sabu",
    # Scam
    "penipuan", "money game", "ponzi",
    # Political
    "presiden bodoh", "demo rusuh",
    # Competitor attacks
    "produk sampah", "jangan beli",
]

# Safe replacement templates
SAFE_REPLACEMENTS: list[str] = [
    "Wah, maaf ya kak, aku lanjut ke produk berikutnya ya!",
    "Kak, yuk kita bahas produk yang lagi promo deh!",
    "Oke kak, kita skip dulu ya, ada yang mau tanya tentang produk?",
    "Hmm, kita ganti topik ya kak! Siapa yang sudah checkout?",
]


@dataclass
class SafetyResult:
    """Result of content safety check."""

    safe: bool
    original_text: str
    filtered_text: str
    trigger_type: str = ""  # keyword_blacklist | pattern | moderation_api
    triggered_keywords: list[str] | None = None
    processing_ms: float = 0.0


class SafetyFilter:
    """Content safety filter with local blacklist + pattern matching.

    Checks LLM output before TTS to prevent banned content.
    All incidents are logged for audit (Req 32.4).
    """

    def __init__(
        self,
        extra_blacklist: list[str] | None = None,
        safe_replies: list[str] | None = None,
    ) -> None:
        self.blacklist = BLACKLIST_KEYWORDS.copy()
        if extra_blacklist:
            self.blacklist.extend(extra_blacklist)

        self.safe_replies = safe_replies or SAFE_REPLACEMENTS.copy()
        self._incident_count = 0
        self._reply_index = 0

        # Compile regex for faster matching
        pattern = "|".join(re.escape(kw) for kw in self.blacklist)
        self._pattern = re.compile(pattern, re.IGNORECASE)

        logger.info("safety_filter_init", blacklist_size=len(self.blacklist))

    def check(self, text: str) -> SafetyResult:
        """Check text for safety violations.

        Args:
            text: Text to check (usually LLM output before TTS).

        Returns:
            SafetyResult with filtering decision.
        """
        start = time.time()

        # Check keyword blacklist
        matches = self._pattern.findall(text)
        if matches:
            safe_reply = self._get_safe_reply()
            processing_ms = (time.time() - start) * 1000
            self._incident_count += 1

            logger.warning(
                "safety_triggered",
                trigger="keyword_blacklist",
                keywords=matches,
                original_len=len(text),
                incident_number=self._incident_count,
            )

            return SafetyResult(
                safe=False,
                original_text=text,
                filtered_text=safe_reply,
                trigger_type="keyword_blacklist",
                triggered_keywords=matches,
                processing_ms=processing_ms,
            )

        # Check for excessive caps (likely yelling/aggressive)
        if len(text) > 20:
            upper_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if upper_ratio > 0.7:
                safe_reply = self._get_safe_reply()
                processing_ms = (time.time() - start) * 1000
                self._incident_count += 1

                logger.warning(
                    "safety_triggered",
                    trigger="excessive_caps",
                    upper_ratio=round(upper_ratio, 2),
                )

                return SafetyResult(
                    safe=False,
                    original_text=text,
                    filtered_text=safe_reply,
                    trigger_type="pattern",
                    processing_ms=processing_ms,
                )

        processing_ms = (time.time() - start) * 1000
        return SafetyResult(
            safe=True,
            original_text=text,
            filtered_text=text,
            processing_ms=processing_ms,
        )

    def _get_safe_reply(self) -> str:
        """Get next safe replacement (round-robin)."""
        reply = self.safe_replies[self._reply_index % len(self.safe_replies)]
        self._reply_index += 1
        return reply

    @property
    def incident_count(self) -> int:
        return self._incident_count
