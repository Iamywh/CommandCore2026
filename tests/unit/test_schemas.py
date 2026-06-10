"""
Tests for schemas and data validation.
"""

import pytest
from uuid import UUID

from app.schemas import (
    AgentName,
    ApprovalStatus,
    ConversationContext,
    FinalResponse,
    Message,
    OrbState,
    ToolCall,
    ToolName,
    UserRequest,
    ApprovalRequest,
    ToolResult,
)


class TestUserRequest:
    """Tests for UserRequest schema."""

    def test_create_basic_request(self):
        """Test creating a basic user request."""
        request = UserRequest(text="Hello, JARVIS")
        assert request.text == "Hello, JARVIS"
        assert request.voice_input is False
        assert isinstance(request.id, UUID)

    def test_request_with_metadata(self):
        """Test user request with metadata."""
        metadata = {"source": "voice", "confidence": 0.95}
        request = UserRequest(text="Test", voice_input=True, metadata=metadata)
        assert request.metadata == metadata
        assert request.voice_input is True

    def test_request_serialization(self):
        """Test serializing/deserializing request."""
        request = UserRequest(text="Hello")
        data = request.model_dump()
        reconstructed = UserRequest(**data)
        assert reconstructed.text == request.text


class TestMessage:
    """Tests for Message schema."""

    def test_create_directed_message(self):
        """Test creating a directed message."""
        message = Message(
            sender=AgentName.DIRECTOR,
            recipient=AgentName.DEV,
            content="Analyze this code",
        )
        assert message.sender == AgentName.DIRECTOR
        assert message.recipient == AgentName.DEV
        assert message.content == "Analyze this code"

    def test_create_broadcast_message(self):
        """Test creating a broadcast message (no recipient)."""
        message = Message(
            sender=AgentName.DIRECTOR,
            content="Task update for all agents",
        )
        assert message.recipient is None
        assert message.content == "Task update for all agents"

    def test_message_threading(self):
        """Test message threading with parent_id."""
        parent_msg = Message(
            sender=AgentName.DEV,
            recipient=AgentName.DIRECTOR,
            content="Analysis complete",
        )
        
        response = Message(
            sender=AgentName.DIRECTOR,
            recipient=AgentName.DEV,
            content="Thank you",
            parent_id=parent_msg.id,
        )
        
        assert response.parent_id == parent_msg.id


class TestConversationContext:
    """Tests for ConversationContext schema."""

    def test_create_conversation(self):
        """Test creating a conversation context."""
        request = UserRequest(text="What is JARVIS?")
        context = ConversationContext(user_request=request)
        
        assert context.user_request.text == "What is JARVIS?"
        assert len(context.messages) == 0
        assert context.final_response is None

    def test_add_message_to_context(self):
        """Test adding messages to conversation."""
        request = UserRequest(text="Test")
        context = ConversationContext(user_request=request)
        
        message = Message(
            sender=AgentName.DIRECTOR,
            content="Processing...",
        )
        context.add_message(message)
        
        assert len(context.messages) == 1
        assert context.messages[0].content == "Processing..."

    def test_add_tool_result(self):
        """Test adding tool results to conversation."""
        from datetime import datetime
        
        request = UserRequest(text="Test")
        context = ConversationContext(user_request=request)
        
        tool_call = ToolCall(tool=ToolName.SHELL, parameters={"cmd": "ls"})
        result = ToolResult(
            tool_call_id=tool_call.id,
            tool=ToolName.SHELL,
            success=True,
            output="file1\nfile2",
        )
        context.add_tool_result(result)
        
        assert len(context.tool_results) == 1


class TestToolCall:
    """Tests for ToolCall schema."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            tool=ToolName.GIT,
            parameters={"cmd": "status"},
            approval_required=True,
        )
        assert call.tool == ToolName.GIT
        assert call.parameters == {"cmd": "status"}
        assert call.approval_status == ApprovalStatus.PENDING

    def test_tool_parameters(self):
        """Test tool call with complex parameters."""
        call = ToolCall(
            tool=ToolName.SHELL,
            parameters={
                "cmd": "python test.py",
                "cwd": "/home/user",
                "timeout": 30,
            },
        )
        assert call.parameters["cmd"] == "python test.py"
        assert call.parameters["timeout"] == 30


class TestApprovalWorkflow:
    """Tests for approval request/response workflow."""

    def test_approval_request_creation(self):
        """Test creating an approval request."""
        from app.schemas import ApprovalRequest
        
        tool_call = ToolCall(
            tool=ToolName.SHELL,
            parameters={"cmd": "rm -rf /"},
        )
        
        approval_req = ApprovalRequest(
            tool_call_id=tool_call.id,
            agent=AgentName.DEV,
            description="Delete entire root filesystem",
            risk_level="critical",
            tool_call=tool_call,
        )
        
        assert approval_req.risk_level == "critical"
        assert approval_req.agent == AgentName.DEV

    def test_approval_response(self):
        """Test creating an approval response."""
        from app.schemas import ApprovalResponse
        
        approval_req = ApprovalRequest(
            tool_call_id=UUID(int=0),
            agent=AgentName.DEV,
            description="Test",
            tool_call=ToolCall(tool=ToolName.SHELL, parameters={}),
        )
        
        response = ApprovalResponse(
            approval_request_id=approval_req.id,
            approved=False,
            reason="Too risky",
            approved_by="user",
        )
        
        assert response.approved is False
        assert response.reason == "Too risky"


class TestFinalResponse:
    """Tests for FinalResponse schema."""

    def test_create_response(self):
        """Test creating a final response."""
        request = UserRequest(text="What is code?")
        response = FinalResponse(
            request_id=request.id,
            response_text="Code is instructions for computers.",
            agent=AgentName.DIRECTOR,
        )
        
        assert response.response_text == "Code is instructions for computers."
        assert response.agent == AgentName.DIRECTOR


class TestEnums:
    """Tests for enum schemas."""

    def test_agent_names(self):
        """Test AgentName enum."""
        assert AgentName.DIRECTOR.value == "director"
        assert AgentName.DEV.value == "dev"
        assert AgentName.CTO.value == "cto"
        assert AgentName.BUSINESS.value == "business"
        assert AgentName.NOTES.value == "notes"

    def test_orb_states(self):
        """Test OrbState enum."""
        assert OrbState.IDLE.value == "idle"
        assert OrbState.LISTENING.value == "listening"
        assert OrbState.THINKING.value == "thinking"
        assert OrbState.SPEAKING.value == "speaking"
        assert OrbState.ERROR.value == "error"

    def test_tool_names(self):
        """Test ToolName enum."""
        assert ToolName.SHELL.value == "shell"
        assert ToolName.GIT.value == "git"
        assert ToolName.FILESYSTEM.value == "filesystem"

    def test_approval_status(self):
        """Test ApprovalStatus enum."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"


class TestToolResult:
    """Tests for ToolResult schema."""

    def test_successful_result(self):
        """Test successful tool result."""
        from app.schemas import ToolResult
        
        result = ToolResult(
            tool_call_id=UUID(int=0),
            tool=ToolName.SHELL,
            success=True,
            output="Command executed",
            execution_time_ms=100.5,
        )
        
        assert result.success is True
        assert result.output == "Command executed"
        assert result.error is None

    def test_failed_result(self):
        """Test failed tool result."""
        from app.schemas import ToolResult
        
        result = ToolResult(
            tool_call_id=UUID(int=0),
            tool=ToolName.SHELL,
            success=False,
            output=None,
            error="Command not found",
            execution_time_ms=50.0,
        )
        
        assert result.success is False
        assert result.error == "Command not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
