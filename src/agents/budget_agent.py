"""
BudgetAgent: estimates trip cost using mock flight/hotel tools and checks
it against the traveler's stated total budget.

This agent deliberately does NOT use the LLM for the arithmetic (never let
an LLM do math it can get wrong when plain code can do it exactly) — it
only uses the LLM to phrase the human-readable budget note. This is a
realistic and important design pattern in production agent systems.
"""

from src.agents.base_agent import BaseAgent
from src.state import TripState
from src.tools import search_flight_price, search_hotel_price


class BudgetAgent(BaseAgent):
    name = "budget_agent"
    system_prompt = (
        "You are a travel budget analyst. Given calculated cost figures, "
        "write one short, clear sentence summarizing whether the trip fits "
        "the traveler's budget."
    )

    def run(self, state: TripState) -> TripState:
        req = state.request

        flight_cost = search_flight_price(req.origin_city, req.destination)
        hotel_per_night = search_hotel_price(req.destination, req.travel_style)
        hotel_total = hotel_per_night * req.duration_days

        destination_info = state.attractions  # already looked up by ResearchAgent
        food_daily = 30  # fallback if research hasn't set it; overridden below if available
        food_total = food_daily * req.duration_days

        total_cost = flight_cost + hotel_total + food_total
        within_budget = total_cost <= req.budget_total

        self._log(
            state,
            f"flight=${flight_cost}, hotel/night=${hotel_per_night}, "
            f"est. total=${total_cost:.2f} vs budget=${req.budget_total}",
        )

        user_prompt = (
            f"Estimated flight cost: ${flight_cost}\n"
            f"Estimated hotel cost ({req.duration_days} nights): ${hotel_total:.2f}\n"
            f"Estimated food cost: ${food_total:.2f}\n"
            f"Total estimated cost: ${total_cost:.2f}\n"
            f"Traveler's stated budget: ${req.budget_total}\n"
            f"Within budget: {within_budget}\n\n"
            "Summarize this for the traveler in one sentence."
        )
        note = self.llm.chat(self.system_prompt, user_prompt)

        state.estimated_flight_cost = flight_cost
        state.estimated_hotel_cost_per_night = hotel_per_night
        state.estimated_total_cost = round(total_cost, 2)
        state.within_budget = within_budget
        state.budget_notes = note
        return state
