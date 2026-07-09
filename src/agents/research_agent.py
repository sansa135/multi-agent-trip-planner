"""
ResearchAgent: gathers destination information.

Calls a (mock) external tool for raw facts, then uses the LLM to turn
those facts into a short research brief the ItineraryAgent can use.
"""

from src.agents.base_agent import BaseAgent
from src.state import TripState
from src.tools import lookup_destination_info


class ResearchAgent(BaseAgent):
    name = "research_agent"
    system_prompt = (
        "You are a travel research specialist. Given raw destination data, "
        "write a concise research brief covering must-see attractions, "
        "general vibe, and practical tips."
    )

    def run(self, state: TripState) -> TripState:
        info = lookup_destination_info(state.request.destination)
        self._log(state, f"looked up destination data for '{state.request.destination}'")

        user_prompt = (
            f"Destination: {state.request.destination}\n"
            f"Traveler interests: {', '.join(state.request.interests)}\n"
            f"Known attractions: {', '.join(info['attractions'])}\n"
            f"Avg daily food cost: ${info['avg_daily_food_cost']}\n\n"
            "Write a short research brief for the itinerary planner."
        )
        brief = self.llm.chat(self.system_prompt, user_prompt)

        state.research_notes = brief
        state.attractions = info["attractions"]
        self._log(state, "research brief generated")
        return state
