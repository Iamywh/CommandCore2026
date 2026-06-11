"""
Data models and schemas for JARVIS2026.

Uses Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class AgentName(StrEnum):
    """Available agents in the system."""

    DIRECTOR = "director"
    DEV = "dev"
    CTO = "cto"
    BUSINESS = "business"
    NOTES = "notes"


class OrbState(StrEnum):
    """Possible states of the animated orb UI."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


class ToolName(StrEnum):
    """Available tools that agents can use."""

    SHELL = "shell"
    GIT = "git"
    GITHUB = "github"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    NOTES = "notes_tool"
    MEMORY = "memory"


class ApprovalStatus(StrEnum):
    """Status of a tool execution approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


class Message(BaseModel):
    """Core message format for inter-agent communication."""

    id: UUID = Field(default_factory=uuid4, description="Unique message ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender: AgentName
    recipient: AgentName | None = None  # None means broadcast
    content: str = Field(description="Message body")
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_id: UUID | None = None  # For message threading

    model_config = ConfigDict(use_enum_values=False)


class UserRequest(BaseModel):
    """Initial user request to the system."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    text: str = Field(description="User's input text")
    voice_input: bool = Field(default=False, description="Whether input was via voice")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: AgentName
    request_id: UUID
    response_text: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_approval: bool = Field(default=False)
    tool_calls: list["ToolCall"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Request to execute a tool."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool: ToolName
    parameters: dict[str, Any] = Field(description="Tool parameters")
    approval_required: bool = Field(default=True)
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)


class ToolResult(BaseModel):
    """Result of tool execution."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_call_id: UUID
    tool: ToolName
    success: bool
    output: Any
    error: str | None = None
    execution_time_ms: float = Field(default=0.0)


class ApprovalRequest(BaseModel):
    """Request for human approval of an action."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_call_id: UUID
    agent: AgentName
    description: str = Field(description="Human-readable description of what needs approval")
    risk_level: str = Field(default="medium")  # low, medium, high, critical
    tool_call: ToolCall


class ApprovalResponse(BaseModel):
    """Human's approval decision."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    approval_request_id: UUID
    approved: bool
    reason: str | None = None
    approved_by: str | None = None


class FinalResponse(BaseModel):
    """Final response to the user."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: UUID
    response_text: str
    agent: AgentName = Field(default=AgentName.DIRECTOR)
    tool_results: list[ToolResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Context for maintaining conversation state."""

    conversation_id: UUID = Field(default_factory=uuid4)
    user_request: UserRequest
    messages: list[Message] = Field(default_factory=list)
    agent_responses: list[AgentResponse] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    approval_requests: list[ApprovalRequest] = Field(default_factory=list)
    final_response: FinalResponse | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        """Add a message to conversation history."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def add_tool_result(self, result: ToolResult) -> None:
        """Add a tool result."""
        self.tool_results.append(result)
        self.updated_at = datetime.utcnow()


class RoutingDecision(BaseModel):
    """Decision made by director about which agent should handle the request."""

    request_id: UUID
    primary_agent: AgentName
    secondary_agents: list[AgentName] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = Field(description="Why this agent was chosen")
    matched_keywords: list[str] = Field(default_factory=list)


# Update forward references
Message.model_rebuild()
AgentResponse.model_rebuild()
