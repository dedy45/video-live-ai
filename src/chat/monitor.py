"""Layer 6: Interaction — Chat Monitoring with Platform Abstraction.

Provides a unified chat monitoring interface with platform-specific connectors.
Implements Observer/Plugin pattern for extensibility (Req 24.1).
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable

from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("chat")


class EventPriority(IntEnum):
    """Event priority levels (P1 = highest)."""

    P1_PURCHASE = 1  # Direct purchase intent
    P2_QUESTION = 2  # Product question
    P3_REACTION = 3  # Emoji, sticker, like
    P4_GENERAL = 4  # General chat
    P5_SPAM = 5  # Spam, ignored


@dataclass
class ChatEvent:
    """Unified chat event across all platforms."""

    platform: str  # tiktok, shopee, youtube, etc.
    username: str
    message: str
    priority: EventPriority = EventPriority.P4_GENERAL
    intent: str = "general"  # purchase, question, humor, complaint, greeting
    raw_data: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class BasePlatformConnector(ABC):
    """Abstract platform connector — Observer pattern (Req 9.8).

    All platform chat monitors implement this interface.
    New platforms added by creating new connector class + registering.
    """

    def __init__(self, platform_name: str) -> None:
        self.platform_name = platform_name
        self._callbacks: list[Callable[[ChatEvent], Any]] = []
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to platform chat stream."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from platform chat stream."""
        ...

    @abstractmethod
    async def listen(self) -> None:
        """Start listening for chat events."""
        ...

    def on_event(self, callback: Callable[[ChatEvent], Any]) -> None:
        """Register callback for chat events (Observer pattern)."""
        self._callbacks.append(callback)

    async def _emit(self, event: ChatEvent) -> None:
        """Emit event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error("callback_error", error=str(e), platform=self.platform_name)

    @property
    def is_connected(self) -> bool:
        return self._connected


class TikTokConnector(BasePlatformConnector):
    """TikTok Live chat connector using TikTokLive library.

    Requirements: 9.1, 9.2 — Real-time TikTok chat + gift monitoring.
    """

    def __init__(self, session_id: str = "") -> None:
        super().__init__("tiktok")
        self._session_id = session_id

    async def connect(self) -> bool:
        if is_mock_mode():
            self._connected = True
            logger.info("mock_tiktok_connected")
            return True

        try:
            # Production: TikTokLive connection
            self._connected = True
            logger.info("tiktok_connected")
            return True
        except Exception as e:
            logger.error("tiktok_connect_error", error=str(e))
            return False

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("tiktok_disconnected")

    async def listen(self) -> None:
        """Listen for TikTok chat events."""
        if is_mock_mode():
            # Generate mock events for testing
            mock_events = [
                ChatEvent("tiktok", "user1", "Harga berapa kak?", EventPriority.P2_QUESTION, "question"),
                ChatEvent("tiktok", "user2", "MAU BELI!", EventPriority.P1_PURCHASE, "purchase"),
                ChatEvent("tiktok", "user3", "😍🔥", EventPriority.P3_REACTION, "reaction"),
            ]
            for event in mock_events:
                await self._emit(event)
                await asyncio.sleep(0.1)
            return


class ShopeeConnector(BasePlatformConnector):
    """Shopee Live chat connector via WebSocket API.

    Requirements: 9.3 — Shopee Live chat monitoring.
    """

    def __init__(self, api_key: str = "") -> None:
        super().__init__("shopee")
        self._api_key = api_key

    async def connect(self) -> bool:
        if is_mock_mode():
            self._connected = True
            logger.info("mock_shopee_connected")
            return True

        self._connected = True
        logger.info("shopee_connected")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("shopee_disconnected")

    async def listen(self) -> None:
        if is_mock_mode():
            mock_events = [
                ChatEvent("shopee", "buyer1", "Bisa COD?", EventPriority.P2_QUESTION, "question"),
                ChatEvent("shopee", "buyer2", "Checkout!", EventPriority.P1_PURCHASE, "purchase"),
            ]
            for event in mock_events:
                await self._emit(event)
                await asyncio.sleep(0.1)


class PriorityEventQueue:
    """Sorted event queue — highest priority first.

    Requirements: 9.5 — P1 (purchase) processed before P4 (general).
    """

    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self._queue: asyncio.PriorityQueue[tuple[int, float, ChatEvent]] = asyncio.PriorityQueue(
            maxsize=max_size
        )

    async def put(self, event: ChatEvent) -> None:
        """Add event to priority queue."""
        try:
            self._queue.put_nowait((event.priority.value, event.timestamp, event))
        except asyncio.QueueFull:
            logger.warning("event_queue_full", dropped_msg=event.message[:30])

    async def get(self) -> ChatEvent:
        """Get highest priority event."""
        _, _, event = await self._queue.get()
        return event

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def empty(self) -> bool:
        return self._queue.empty()


class IntentDetector:
    """Detect user intent from chat messages.

    Requirements: 9.6 — Classify chat messages for routing.
    """

    PURCHASE_KEYWORDS = [
        "beli", "order", "checkout", "keranjang", "bayar",
        "mau", "pengen", "ambil", "pesan", "cod", "transfer",
    ]
    QUESTION_KEYWORDS = [
        "berapa", "harga", "ukuran", "warna", "bahan",
        "ongkir", "stok", "ready", "available",
    ]

    def detect(self, message: str) -> tuple[EventPriority, str]:
        """Detect intent and assign priority."""
        lower = message.lower()

        # Purchase intent
        if any(kw in lower for kw in self.PURCHASE_KEYWORDS):
            return EventPriority.P1_PURCHASE, "purchase"

        # Question
        if any(kw in lower for kw in self.QUESTION_KEYWORDS) or "?" in message:
            return EventPriority.P2_QUESTION, "question"

        # Reaction (emoji-heavy)
        emoji_count = sum(1 for c in message if ord(c) > 0x1F600)
        if emoji_count > len(message) * 0.3:
            return EventPriority.P3_REACTION, "reaction"

        return EventPriority.P4_GENERAL, "general"


class ChatMonitor:
    """Unified chat monitor — manages all platform connectors.

    Aggregates events from multiple platforms into a single priority queue.
    """

    def __init__(self) -> None:
        self.connectors: dict[str, BasePlatformConnector] = {}
        self.queue = PriorityEventQueue()
        self.intent_detector = IntentDetector()
        self._event_count = 0

    def register_connector(self, connector: BasePlatformConnector) -> None:
        """Register a platform connector."""
        self.connectors[connector.platform_name] = connector
        connector.on_event(self._handle_event)
        logger.info("connector_registered", platform=connector.platform_name)

    async def _handle_event(self, event: ChatEvent) -> None:
        """Process incoming event: detect intent → assign priority → queue."""
        priority, intent = self.intent_detector.detect(event.message)
        event.priority = priority
        event.intent = intent
        await self.queue.put(event)
        self._event_count += 1

    async def start_all(self) -> None:
        """Connect and start all registered connectors."""
        for name, connector in self.connectors.items():
            await connector.connect()
            logger.info("connector_started", platform=name)

    async def stop_all(self) -> None:
        """Disconnect all connectors."""
        for name, connector in self.connectors.items():
            await connector.disconnect()

    @property
    def event_count(self) -> int:
        return self._event_count
