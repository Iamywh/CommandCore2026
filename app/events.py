"""
Event system for JARVIS2026.

Provides a callback-based event bus for system-wide communication.
"""

from typing import Any, Callable, Optional
from uuid import UUID

from app.schemas import (
    AgentResponse,
    ApprovalRequest,
    ApprovalResponse,
    ConversationContext,
    FinalResponse,
    Message,
    OrbState,
    ToolCall,
    ToolResult,
    UserRequest,
)


class EventType:
    """Event type constants."""

    # Lifecycle events
    APP_STARTED = "app.started"
    APP_STOPPED = "app.stopped"

    # User input events
    USER_INPUT_RECEIVED = "user.input.received"
    SPEECH_INPUT_STARTED = "speech.input.started"
    SPEECH_INPUT_ENDED = "speech.input.ended"

    # Routing events
    ROUTING_DECISION_MADE = "routing.decision.made"
    AGENT_DELEGATED = "agent.delegated"

    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_RESPONSE_RECEIVED = "agent.response.received"
    AGENT_ERROR = "agent.error"

    # Tool events
    TOOL_EXECUTION_REQUESTED = "tool.execution.requested"
    TOOL_APPROVAL_NEEDED = "tool.approval.needed"
    TOOL_APPROVED = "tool.approved"
    TOOL_REJECTED = "tool.rejected"
    TOOL_EXECUTION_STARTED = "tool.execution.started"
    TOOL_EXECUTION_COMPLETED = "tool.execution.completed"
    TOOL_EXECUTION_FAILED = "tool.execution.failed"

    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"

    # Response events
    FINAL_RESPONSE_READY = "response.final.ready"

    # UI events
    ORB_STATE_CHANGED = "ui.orb.state.changed"
    UI_UPDATE_REQUESTED = "ui.update.requested"

    # Memory events
    MEMORY_SAVED = "memory.saved"
    JOURNAL_ENTRY_CREATED = "journal.entry.created"


class Event:
    """Base event class."""

    def __init__(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str = "system",
    ):
        self.event_type = event_type
        self.data = data
        self.source = source

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, source={self.source})"


class EventCallback:
    """Wrapper for event callbacks with metadata."""

    def __init__(
        self,
        callback: Callable,
        event_types: list[str],
        priority: int = 0,
    ):
        self.callback = callback
        self.event_types = event_types
        self.priority = priority

    async def __call__(self, event: Event) -> None:
        """Execute the callback."""
        if event.event_type in self.event_types:
            await self.callback(event)


class EventBus:
    """Central event bus for system-wide communication."""

    def __init__(self):
        self._callbacks: dict[str, list[EventCallback]] = {}
        self._event_history: list[Event] = []
        self._max_history = 1000

    def subscribe(
        self,
        event_types: list[str],
        callback: Callable,
        priority: int = 0,
    ) -> Callable:
        """Subscribe to events.

        Args:
            event_types: List of event types to listen for
            callback: Async callable to execute on event
            priority: Higher priority callbacks run first

        Returns:
            The callback for unsubscribing
        """
        event_cb = EventCallback(callback, event_types, priority)

        for event_type in event_types:
            if event_type not in self._callbacks:
                self._callbacks[event_type] = []
            self._callbacks[event_type].append(event_cb)
            # Sort by priority (higher first)
            self._callbacks[event_type].sort(key=lambda x: -x.priority)

        return callback

    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Unsubscribe from events."""
        if event_type not in self._callbacks:
            return False

        self._callbacks[event_type] = [
            cb for cb in self._callbacks[event_type] if cb.callback != callback
        ]
        return True

    async def emit(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str = "system",
    ) -> None:
        """Emit an event and notify all listeners.

        Args:
            event_type: Type of event
            data: Event data payload
            source: Source of the event
        """
        event = Event(event_type, data, source)
        self._event_history.append(event)

        # Keep history under control
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history :]

        # Execute callbacks for this event type
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    await self.emit(
                        EventType.APP_STARTED,
                        {"error": f"Callback error: {e}"},
                        source="event_bus",
                    )

    def get_history(self, event_type: Optional[str] = None) -> list[Event]:
        """Get event history, optionally filtered by type."""
        if event_type is None:
            return self._event_history.copy()
        return [e for e in self._event_history if e.event_type == event_type]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


class EventEmitter:
    """Convenience wrapper for emitting common events."""

    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or get_event_bus()

    async def user_input_received(self, request: UserRequest) -> None:
        """Emit user input event."""
        await self.bus.emit(
            EventType.USER_INPUT_RECEIVED,
            {"request": request.model_dump()},
            source="input_handler",
        )

    async def routing_decision_made(self, decision: Any) -> None:
        """Emit routing decision event."""
        await self.bus.emit(
            EventType.ROUTING_DECISION_MADE,
            {"decision": decision.model_dump() if hasattr(decision, "model_dump") else decision},
            source="director",
        )

    async def agent_response_received(self, response: AgentResponse) -> None:
        """Emit agent response event."""
        await self.bus.emit(
            EventType.AGENT_RESPONSE_RECEIVED,
            {"response": response.model_dump()},
            source=response.agent.value,
        )

    async def tool_approval_needed(self, request: ApprovalRequest) -> None:
        """Emit tool approval needed event."""
        await self.bus.emit(
            EventType.TOOL_APPROVAL_NEEDED,
            {"approval_request": request.model_dump()},
            source="approval_system",
        )

    async def tool_execution_completed(self, result: ToolResult) -> None:
        """Emit tool execution completed event."""
        await self.bus.emit(
            EventType.TOOL_EXECUTION_COMPLETED,
            {"result": result.model_dump()},
            source="tool_executor",
        )

    async def final_response_ready(self, response: FinalResponse) -> None:
        """Emit final response ready event."""
        await self.bus.emit(
            EventType.FINAL_RESPONSE_READY,
            {"response": response.model_dump()},
            source="director",
        )

    async def orb_state_changed(self, state: OrbState) -> None:
        """Emit orb state change event."""
        await self.bus.emit(
            EventType.ORB_STATE_CHANGED,
            {"state": state.value},
            source="ui",
        )

    async def journal_entry_created(self, entry_id: UUID, content: str) -> None:
        """Emit journal entry created event."""
        await self.bus.emit(
            EventType.JOURNAL_ENTRY_CREATED,
            {"entry_id": str(entry_id), "content": content},
            source="memory",
        )
