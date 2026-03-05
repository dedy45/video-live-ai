"""Orchestrator — State Machine & Main Event Loop.

Ties all 7 layers together into a cohesive live commerce system.
Manages state transitions: SELLING ↔ REACTING ↔ ENGAGING.
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any

from src.brain import LLMRouter, PersonaEngine, SafetyFilter
from src.brain.adapters.base import TaskType
from src.chat.monitor import ChatEvent, ChatMonitor, EventPriority
from src.commerce.manager import Product, ProductManager
from src.config import get_config, is_mock_mode
from src.utils.logging import generate_trace_id, get_logger

logger = get_logger("orchestrator")


class SystemState(str, Enum):
    """Main state machine states."""

    SELLING = "SELLING"      # 80% — presenting products
    REACTING = "REACTING"    # 15% — responding to chat
    ENGAGING = "ENGAGING"    # 5% — filler, humor, engagement
    IDLE = "IDLE"            # System idle


class Orchestrator:
    """Main orchestrator — coordinates all 7 layers.

    State machine with event-driven transitions:
    - SELLING: Product presentation with pre-rendered scripts
    - REACTING: Real-time response to high-priority chat events
    - ENGAGING: Filler content for audience retention
    """

    def __init__(self) -> None:
        self.state = SystemState.IDLE
        self.router = LLMRouter()
        self.persona = PersonaEngine()
        self.safety = SafetyFilter()
        self.chat_monitor = ChatMonitor()
        self.product_manager = ProductManager()

        self._running = False
        self._tick_count = 0
        self._state_enter_time = time.time()
        self._viewer_count = 0

        logger.info("orchestrator_init")

    async def start(self) -> None:
        """Start the main event loop."""
        self._running = True
        self.state = SystemState.SELLING
        self._state_enter_time = time.time()

        logger.info("orchestrator_started", state=self.state.value)

        # Start chat monitors
        await self.chat_monitor.start_all()

        # Main loop
        while self._running:
            await self._tick()
            await asyncio.sleep(0.1)  # 10Hz tick rate

    async def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        self._running = False
        await self.chat_monitor.stop_all()
        logger.info("orchestrator_stopped", ticks=self._tick_count)

    async def _tick(self) -> None:
        """Main tick — evaluate state and process events."""
        self._tick_count += 1

        # Check for high-priority chat events
        if not self.chat_monitor.queue.empty:
            event = await self.chat_monitor.queue.get()

            if event.priority <= EventPriority.P2_QUESTION:
                # High priority → switch to REACTING
                await self._transition(SystemState.REACTING)
                await self._handle_chat_reaction(event)
                return

        # State-specific logic
        if self.state == SystemState.SELLING:
            await self._handle_selling()
        elif self.state == SystemState.REACTING:
            await self._handle_reacting_timeout()
        elif self.state == SystemState.ENGAGING:
            await self._handle_engaging()

    async def _transition(self, new_state: SystemState) -> None:
        """Transition to a new state."""
        if new_state != self.state:
            old = self.state
            time_in_state = time.time() - self._state_enter_time
            self.state = new_state
            self._state_enter_time = time.time()
            logger.info(
                "state_transition",
                old=old.value,
                new=new_state.value,
                duration_sec=round(time_in_state, 1),
            )

    async def _handle_selling(self) -> None:
        """SELLING state — present products."""
        # Check if product rotation is needed
        if self.product_manager.should_rotate():
            product = self.product_manager.rotate_next()
            if product:
                await self._generate_selling_content(product)

        # After extended selling, briefly engage
        time_selling = time.time() - self._state_enter_time
        if time_selling > 60:  # After 60 seconds, brief engagement
            await self._transition(SystemState.ENGAGING)

    async def _handle_chat_reaction(self, event: ChatEvent) -> None:
        """Process a high-priority chat event."""
        trace_id = generate_trace_id()

        # Build reaction prompt
        product = self.product_manager.get_current_product()
        product_ctx = f"{product.name} - {product.price_formatted}" if product else ""

        system_prompt = self.persona.build_system_prompt(
            state="REACTING",
            product_context=product_ctx,
        )

        # Generate response via LLM
        response = await self.router.route(
            system_prompt=system_prompt,
            user_prompt=f"Viewer '{event.username}' berkata: {event.message}",
            task_type=TaskType.CHAT_REPLY,
            trace_id=trace_id,
        )

        # Safety check
        safety_result = self.safety.check(response.text)
        final_text = safety_result.filtered_text

        logger.info(
            "chat_reaction",
            username=event.username,
            response_len=len(final_text),
            safe=safety_result.safe,
            trace_id=trace_id,
        )

        # Return to selling after reaction
        await self._transition(SystemState.SELLING)

    async def _handle_reacting_timeout(self) -> None:
        """Timeout from REACTING → back to SELLING."""
        time_in_state = time.time() - self._state_enter_time
        if time_in_state > 5:  # Max 5 seconds in REACTING
            await self._transition(SystemState.SELLING)

    async def _handle_engaging(self) -> None:
        """ENGAGING state — filler content.

        Performance fix: removed blocking asyncio.sleep(2) from the hot path.
        The state machine naturally returns to SELLING after the next tick
        via _handle_selling; the engagement timeout is handled by checking
        time_in_state in the SELLING handler.
        """
        trace_id = generate_trace_id()

        system_prompt = self.persona.build_system_prompt(
            state="ENGAGING",
            viewer_count=self._viewer_count,
        )
        filler_prompt = self.persona.get_filler_prompt()

        response = await self.router.route(
            system_prompt=system_prompt,
            user_prompt=filler_prompt,
            task_type=TaskType.FILLER,
            trace_id=trace_id,
        )

        safety_result = self.safety.check(response.text)
        logger.info("engage_filler", text=safety_result.filtered_text[:50], trace_id=trace_id)

        # Transition back to SELLING immediately — no blocking sleep.
        # The 10Hz tick loop itself provides natural pacing.
        await self._transition(SystemState.SELLING)

    async def _generate_selling_content(self, product: Product) -> None:
        """Generate selling script for a product."""
        trace_id = generate_trace_id()

        system_prompt = self.persona.build_system_prompt(
            state="SELLING",
            product_context=f"{product.name} - {product.price_formatted}",
        )
        script_prompt = self.persona.build_selling_script_prompt(
            product_name=product.name,
            price=product.price,
            features=product.features,
        )

        response = await self.router.route(
            system_prompt=system_prompt,
            user_prompt=script_prompt,
            task_type=TaskType.SELLING_SCRIPT,
            trace_id=trace_id,
        )

        safety_result = self.safety.check(response.text)
        logger.info(
            "selling_script_generated",
            product=product.name,
            script_len=len(safety_result.filtered_text),
            trace_id=trace_id,
        )

    def get_status(self) -> dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "state": self.state.value,
            "tick_count": self._tick_count,
            "time_in_state_sec": round(time.time() - self._state_enter_time, 1),
            "viewer_count": self._viewer_count,
            "chat_queue_size": self.chat_monitor.queue.size,
            "llm_stats": self.router.get_usage_stats(),
            "safety_incidents": self.safety.incident_count,
        }
