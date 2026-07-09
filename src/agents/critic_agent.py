"""
CriticAgent: reviews the draft itinerary against budget and interests.
This is the agent that creates the *loop* in the graph — if it rejects the
plan, the orchestrator routes back to ItineraryAgent for a revision, up to
a max number of retries (to guarantee termination).
"""

from src.agents.base_agent import BaseAgent
from src.state import TripState


class CriticAgent(BaseAgent):
    name = "critic_agent"
    system_prompt = (
        "You are a meticulous critic reviewing a travel itinerary. Check "
        "whether it fits the budget and matches the traveler's interests. "
        "Respond with APPROVED or specific revision requests."
    )

    def run(self, state: TripState) -> TripState:
        user_prompt = (
            f"Itinerary: {state.itinerary}\n"
            f"Within budget: {state.within_budget}\n"
            f"Traveler interests: {', '.join(state.request.interests)}\n\n"
            "Approve or request revisions."
        )
        response = self.llm.chat(self.system_prompt, user_prompt)

        # Simple, explicit approval rule (kept in code, not left to free-text
        # LLM parsing) so the loop-termination logic is deterministic:
        # approve if within budget OR max revisions already reached.
        if state.within_budget or state.revision_count >= state.max_revisions:
            state.approved = True
            state.critique = "APPROVED" if state.within_budget else (
                "APPROVED with budget caveat: over budget after max revisions; "
                "flagged for traveler to adjust dates/style."
            )
            self._log(state, "itinerary approved")
        else:
            state.approved = False
            state.critique = (
                f"Trip is ${state.estimated_total_cost - state.request.budget_total:.2f} "
                "over budget. Consider a shorter trip, lower-cost travel style, "
                "or fewer paid attractions."
            )
            state.revision_count += 1
            self._log(state, f"itinerary rejected: {state.critique}")

        return state
