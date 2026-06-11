"""
Orchestrator for JARVIS2026.

Routes requests to appropriate agents using keyword matching.
"""

from app.events import EventEmitter
from app.schemas import AgentName, RoutingDecision, UserRequest
from app.settings import get_settings


class Orchestrator:
    """Central orchestrator that routes requests to agents."""

    def __init__(self):
        self.settings = get_settings()
        self.emitter = EventEmitter()

    async def route_request(self, request: UserRequest) -> RoutingDecision:
        """Route a user request to the appropriate agent using keyword matching.

        Args:
            request: User request to route

        Returns:
            Routing decision with primary and secondary agents
        """
        text_lower = request.text.lower()

        # Score each agent based on keyword matches
        scores: dict[str, tuple[float, list[str]]] = {}

        for agent_name in ["dev", "cto", "business", "notes"]:
            keywords = self.settings.agents.get_keywords_for_agent(agent_name)
            matched = [kw for kw in keywords if kw in text_lower]
            # Each matched keyword contributes significant weight for MVP routing.
            # Use a simple multiplier and cap at 1.0 so a single strong keyword
            # can exceed the previous weak fractional score.
            match_score = min(1.0, len(matched) * 0.35)
            scores[agent_name] = (match_score, matched)

        # Sort by score descending
        sorted_agents = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

        # Determine primary and secondary agents
        primary_agent = AgentName.DIRECTOR
        secondary_agents: list[AgentName] = []
        matched_keywords: list[str] = []

        if sorted_agents and sorted_agents[0][1][0] > 0.3:  # Confidence threshold
            _primary_score, keywords = sorted_agents[0][1]
            matched_keywords = keywords

            # Map to enum
            agent_map = {
                "dev": AgentName.DEV,
                "cto": AgentName.CTO,
                "business": AgentName.BUSINESS,
                "notes": AgentName.NOTES,
            }
            primary_agent = agent_map.get(sorted_agents[0][0], AgentName.DIRECTOR)

            # Add secondary agents if they have decent match
            for agent_name, (score, _kws) in sorted_agents[1:]:
                if score > 0.1:
                    secondary_agents.append(agent_map[agent_name])

        decision = RoutingDecision(
            request_id=request.id,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            confidence=sorted_agents[0][1][0] if sorted_agents else 0.0,
            reasoning=f"Routed to {primary_agent.value} based on keyword matching",
            matched_keywords=matched_keywords,
        )

        # Emit routing decision event
        await self.emitter.routing_decision_made(decision)

        return decision

    def classify_intent(self, text: str) -> str:
        """Classify the general intent of the user request.

        Args:
            text: User input text

        Returns:
            Intent classification (query, action, approval, etc)
        """
        text_lower = text.lower()

        if any(word in text_lower for word in ["?", "what", "how", "why", "when", "where"]):
            return "query"
        elif any(word in text_lower for word in ["create", "delete", "modify", "run", "execute"]):
            return "action"
        elif any(word in text_lower for word in ["approve", "yes", "no", "reject"]):
            return "approval"
        elif any(word in text_lower for word in ["save", "remember", "journal", "note"]):
            return "memory"
        else:
            return "general"

    def get_agent_capabilities(self, agent_name: AgentName) -> list[str]:
        """Get the capabilities of an agent.

        Args:
            agent_name: The agent to query

        Returns:
            List of capabilities
        """
        capabilities = {
            AgentName.DIRECTOR: [
                "request_routing",
                "agent_delegation",
                "approval_gate",
                "response_synthesis",
            ],
            AgentName.DEV: [
                "code_analysis",
                "file_modification",
                "git_operations",
                "test_execution",
            ],
            AgentName.CTO: [
                "architecture_design",
                "technical_analysis",
                "scalability_review",
                "security_review",
            ],
            AgentName.BUSINESS: [
                "roadmap_planning",
                "priority_assessment",
                "business_impact",
                "client_communication",
            ],
            AgentName.NOTES: [
                "conversation_summary",
                "journal_creation",
                "memory_persistence",
                "decision_logging",
            ],
        }
        return capabilities.get(agent_name, [])

    def can_agent_use_tool(self, agent_name: AgentName, tool_name: str) -> bool:
        """Check if an agent is allowed to use a tool.

        Args:
            agent_name: The agent
            tool_name: The tool

        Returns:
            True if agent can use tool
        """
        # Basic permissions matrix
        permissions = {
            AgentName.DIRECTOR: ["approval_request"],
            AgentName.DEV: ["shell", "git", "filesystem"],
            AgentName.CTO: ["memory"],
            AgentName.BUSINESS: ["memory"],
            AgentName.NOTES: ["notes_tool", "memory"],
        }

        allowed_tools = permissions.get(agent_name, [])
        return tool_name in allowed_tools
