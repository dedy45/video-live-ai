"""Layer 4: Composition — FFmpeg Video Compositor.

Combines avatar, background, product overlay, and HUD into final video.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import get_config, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("composition")


@dataclass
class CompositionLayout:
    """Layout configuration for video composition layers."""

    resolution: tuple[int, int] = (720, 1280)  # 9:16 portrait
    fps: int = 30
    avatar_position: tuple[int, int] = (480, 800)
    avatar_size: tuple[int, int] = (216, 384)  # 30% of 720x1280
    product_position: tuple[int, int] = (24, 200)
    product_size: tuple[int, int] = (432, 768)  # 60% area


@dataclass
class OverlayConfig:
    """HUD overlay configuration (price tags, CTA, urgency bar)."""

    price_position: tuple[int, int] = (24, 650)
    price_font_size: int = 36
    cta_position: tuple[int, int] = (180, 1100)
    cta_font_size: int = 28
    urgency_position: tuple[int, int] = (180, 50)
    urgency_font_size: int = 24


class FFmpegCompositor:
    """FFmpeg-based video compositor.

    Combines multiple video/image layers into a single output stream.
    Requirements: 5.1 — 7-layer composition, 5.5 — configurable layouts.
    """

    def __init__(self) -> None:
        config = get_config()
        comp_cfg = config.composition
        self.layout = CompositionLayout(
            resolution=tuple(comp_cfg.resolution),
            fps=comp_cfg.fps,
        )
        self.overlay = OverlayConfig()
        self._process: subprocess.Popen[bytes] | None = None
        logger.info(
            "compositor_init",
            resolution=self.layout.resolution,
            fps=self.layout.fps,
        )

    def build_filter_graph(
        self,
        background_path: str,
        product_image_path: str | None = None,
        price_text: str = "",
        cta_text: str = "",
    ) -> str:
        """Build FFmpeg filter graph for layer composition.

        Layers (bottom to top):
        1. Background (720x1280)
        2. Product image (scaled, positioned)
        3. Avatar video (positioned bottom-right)
        4. Price overlay text
        5. CTA overlay text
        6. Urgency bar (optional)
        7. Watermark (optional)
        """
        w, h = self.layout.resolution
        filters: list[str] = []

        # Scale background
        filters.append(f"[0:v]scale={w}:{h}[bg]")

        # Overlay product image
        if product_image_path:
            pw, ph = self.layout.product_size
            px, py = self.layout.product_position
            filters.append(f"[1:v]scale={pw}:{ph}[prod]")
            filters.append(f"[bg][prod]overlay={px}:{py}[with_prod]")
        else:
            filters.append("[bg]copy[with_prod]")

        # Overlay avatar
        ax, ay = self.layout.avatar_position
        aw, ah = self.layout.avatar_size
        filters.append(f"[2:v]scale={aw}:{ah}[avatar]")
        filters.append(f"[with_prod][avatar]overlay={ax}:{ay}[with_avatar]")

        # Add text overlays
        if price_text:
            px, py = self.overlay.price_position
            fs = self.overlay.price_font_size
            filters.append(
                f"[with_avatar]drawtext=text='{price_text}':x={px}:y={py}:"
                f"fontsize={fs}:fontcolor=white:borderw=2:bordercolor=black[with_price]"
            )
        else:
            filters.append("[with_avatar]copy[with_price]")

        if cta_text:
            cx, cy = self.overlay.cta_position
            fs = self.overlay.cta_font_size
            filters.append(
                f"[with_price]drawtext=text='{cta_text}':x={cx}:y={cy}:"
                f"fontsize={fs}:fontcolor=yellow:borderw=2:bordercolor=black[out]"
            )
        else:
            filters.append("[with_price]copy[out]")

        return ";".join(filters)

    async def start_composition(self, output_pipe: str = "pipe:1") -> None:
        """Start the FFmpeg composition process."""
        if is_mock_mode():
            logger.info("mock_compositor_start", msg="Composition skipped in Mock Mode")
            return

        logger.info("compositor_start", output=output_pipe)

    async def stop(self) -> None:
        """Stop the composition process."""
        if self._process:
            self._process.terminate()
            self._process = None
            logger.info("compositor_stopped")

    async def health_check(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
