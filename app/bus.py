"""
Message bus for inter-agent communication.

Provides structured routing and validation for all messages.
"""

import asyncio
from contextlib import suppress

from app.events import EventEmitter, EventType
from app.schemas import AgentName, Message


class MessageBus:
    """Central message bus for agent-to-agent communication."""

    def __init__(self):
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._agent_queues: dict[str, asyncio.Queue] = {}
        self._message_history: list[Message] = []
        self._max_history = 5000
        self._emitter = EventEmitter()
        self._running = False
        self._routing_task: asyncio.Task | None = None

    def register_agent(self, agent_name: AgentName) -> asyncio.Queue:
        """Register an agent to receive messages.

        Args:
            agent_name: Name of the agent

        Returns:
            Queue for this agent to receive messages
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._agent_queues[agent_name.value] = queue
        return queue

    async def send(
        self,
        message: Message,
        timeout: float | None = None,
    ) -> bool:
        """Send a message to the bus.

        Args:
            message: Message to send
            timeout: Optional timeout for sending

        Returns:
            True if sent successfully
        """
        try:
            if timeout:
                await asyncio.wait_for(
                    self._message_queue.put(message),
                    timeout=timeout,
                )
            else:
                await self._message_queue.put(message)

            # Record in history
            self._message_history.append(message)
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history :]

            # Emit event
            await self._emitter.bus.emit(
                EventType.MESSAGE_SENT,
                {
                    "message_id": str(message.id),
                    "sender": message.sender.value,
                    "recipient": message.recipient.value if message.recipient else "broadcast",
                },
                source="bus",
            )

            return True
        except TimeoutError:
            return False

    async def receive(
        self,
        agent_name: AgentName,
        timeout: float | None = None,
    ) -> Message | None:
        """Receive a message for an agent.

        Args:
            agent_name: Agent receiving the message
            timeout: Optional timeout for receiving

        Returns:
            Message if received, None if timeout
        """
        queue = self._agent_queues.get(agent_name.value)
        if queue is None:
            return None

        try:
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()

            # Emit event
            await self._emitter.bus.emit(
                EventType.MESSAGE_RECEIVED,
                {
                    "message_id": str(message.id),
                    "sender": message.sender.value,
                    "recipient": agent_name.value,
                },
                source="bus",
            )

            return message
        except TimeoutError:
            return None

    async def broadcast(self, message: Message) -> None:
        """Broadcast a message to all agents (except sender).

        Args:
            message: Message to broadcast
        """
        for agent_name, queue in self._agent_queues.items():
            if agent_name != message.sender.value:
                with suppress(asyncio.QueueFull):
                    queue.put_nowait(message)

    async def send_to_agent(
        self,
        recipient: AgentName,
        message: Message,
    ) -> bool:
        """Send a message directly to an agent.

        Args:
            recipient: Target agent
            message: Message to send

        Returns:
            True if sent successfully
        """
        queue = self._agent_queues.get(recipient.value)
        if queue is None:
            return False

        try:
            queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            return False

    async def start(self) -> None:
        """Start the message bus routing loop."""
        self._running = True
        self._routing_task = asyncio.create_task(self._routing_loop())

    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False

    async def _routing_loop(self) -> None:
        """Main routing loop for messages."""
        while self._running:
            try:
                # Get message from main queue with timeout to allow checking _running
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0,
                )

                # If recipient is specified, send to that agent
                if message.recipient:
                    await self.send_to_agent(message.recipient, message)
                else:
                    # Broadcast to all agents
                    await self.broadcast(message)

            except TimeoutError:
                continue
            except Exception as e:
                await self._emitter.bus.emit(
                    EventType.APP_STARTED,  # Use as generic error event
                    {"error": f"Bus routing error: {e}"},
                    source="bus",
                )

    def get_history(
        self,
        sender: AgentName | None = None,
        recipient: AgentName | None = None,
        limit: int | None = None,
    ) -> list[Message]:
        """Get message history.

        Args:
            sender: Filter by sender
            recipient: Filter by recipient
            limit: Max number of messages to return

        Returns:
            Filtered message history
        """
        history = self._message_history

        if sender:
            history = [m for m in history if m.sender == sender]

        if recipient:
            history = [m for m in history if m.recipient == recipient]

        if limit:
            history = history[-limit :]

        return history

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()

    def get_queue_sizes(self) -> dict[str, int]:
        """Get current queue sizes for all agents.

        Returns:
            Dict mapping agent names to queue sizes
        """
        return {name: queue.qsize() for name, queue in self._agent_queues.items()}


# Global message bus instance
_message_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """Get or create the global message bus."""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus
