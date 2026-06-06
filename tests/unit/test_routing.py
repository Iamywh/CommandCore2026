"""
Tests for orchestrator routing logic.
"""

import pytest
import asyncio

from app.orchestrator import Orchestrator
from app.schemas import AgentName, RoutingDecision, UserRequest


class TestOrchestratorRouting:
    """Tests for orchestrator request routing."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return Orchestrator()

    @pytest.mark.asyncio
    async def test_route_dev_request(self, orchestrator):
        """Test routing a development request."""
        request = UserRequest(text="Can you fix this Python bug?")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent == AgentName.DEV
        assert decision.confidence > 0.3

    @pytest.mark.asyncio
    async def test_route_cto_request(self, orchestrator):
        """Test routing an architecture request."""
        request = UserRequest(text="What's the best architecture for scaling?")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent == AgentName.CTO
        assert "architecture" in [kw.lower() for kw in decision.matched_keywords]

    @pytest.mark.asyncio
    async def test_route_business_request(self, orchestrator):
        """Test routing a business request."""
        request = UserRequest(text="What should be our priority for next quarter?")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent in [AgentName.BUSINESS, AgentName.DIRECTOR]

    @pytest.mark.asyncio
    async def test_route_notes_request(self, orchestrator):
        """Test routing a notes/memory request."""
        request = UserRequest(text="Save this to my journal: today was productive")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent == AgentName.NOTES
        assert "journal" in [kw.lower() for kw in decision.matched_keywords]

    @pytest.mark.asyncio
    async def test_route_generic_request(self, orchestrator):
        """Test routing a generic request goes to director."""
        request = UserRequest(text="Hello, how are you?")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent == AgentName.DIRECTOR
        assert decision.confidence <= 0.3

    @pytest.mark.asyncio
    async def test_routing_with_multiple_keywords(self, orchestrator):
        """Test routing with multiple matching keywords."""
        request = UserRequest(text="Debug and refactor this Python code")
        decision = await orchestrator.route_request(request)
        
        assert decision.primary_agent == AgentName.DEV
        assert len(decision.matched_keywords) >= 2

    def test_intent_classification_query(self, orchestrator):
        """Test intent classification for queries."""
        intent = orchestrator.classify_intent("What is machine learning?")
        assert intent == "query"

    def test_intent_classification_action(self, orchestrator):
        """Test intent classification for actions."""
        intent = orchestrator.classify_intent("Create a new file named test.py")
        assert intent == "action"

    def test_intent_classification_approval(self, orchestrator):
        """Test intent classification for approvals."""
        intent = orchestrator.classify_intent("Yes, go ahead")
        assert intent == "approval"

    def test_intent_classification_memory(self, orchestrator):
        """Test intent classification for memory operations."""
        intent = orchestrator.classify_intent("Remember this important deadline")
        assert intent == "memory"

    def test_agent_capabilities(self, orchestrator):
        """Test retrieving agent capabilities."""
        dev_caps = orchestrator.get_agent_capabilities(AgentName.DEV)
        assert "code_analysis" in dev_caps
        assert "file_modification" in dev_caps

        cto_caps = orchestrator.get_agent_capabilities(AgentName.CTO)
        assert "architecture_design" in cto_caps

        notes_caps = orchestrator.get_agent_capabilities(AgentName.NOTES)
        assert "journal_creation" in notes_caps

    def test_tool_permissions(self, orchestrator):
        """Test tool permission checking."""
        # Dev can use shell
        assert orchestrator.can_agent_use_tool(AgentName.DEV, "shell")
        
        # Dev can use git
        assert orchestrator.can_agent_use_tool(AgentName.DEV, "git")
        
        # Dev cannot use approval_request
        assert not orchestrator.can_agent_use_tool(AgentName.DEV, "approval_request")
        
        # Director can use approval_request
        assert orchestrator.can_agent_use_tool(AgentName.DIRECTOR, "approval_request")
        
        # Notes can use memory
        assert orchestrator.can_agent_use_tool(AgentName.NOTES, "memory")


class TestRoutingDecision:
    """Tests for RoutingDecision schema."""

    def test_create_routing_decision(self):
        """Test creating a routing decision."""
        request_id = UserRequest(text="test").id
        decision = RoutingDecision(
            request_id=request_id,
            primary_agent=AgentName.DEV,
            confidence=0.85,
            reasoning="Matched development keywords",
            matched_keywords=["code", "debug"],
        )
        
        assert decision.primary_agent == AgentName.DEV
        assert decision.confidence == 0.85
        assert "code" in decision.matched_keywords

    def test_routing_decision_with_secondary(self):
        """Test routing decision with secondary agents."""
        request_id = UserRequest(text="test").id
        decision = RoutingDecision(
            request_id=request_id,
            primary_agent=AgentName.DEV,
            secondary_agents=[AgentName.CTO],
            confidence=0.7,
            reasoning="Could involve architecture",
        )
        
        assert len(decision.secondary_agents) == 1
        assert AgentName.CTO in decision.secondary_agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
