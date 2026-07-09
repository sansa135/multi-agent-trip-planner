"""
ItineraryAgent: combines research notes + budget constraints into a
day-by-day plan. Can be invoked multiple times if the CriticAgent requests
revisions (e.g. to cut cost, or better match stated interests).
"""

from src.agents.base_agent import BaseAgent
from src.state import TripState


class ItineraryAgent(BaseAgent):
    name = "itinerary_agent"
    system_prompt = (
        "You are an itinerary planner. Given research notes, a list of "
        "attractions, and budget constraints, produce a day-by-day plan."
    )

    def run(self, state: TripState) -> TripState:
        req = state.request
        revision_note = ""
        if state.critique and not state.approved:
            revision_note = f"\nPrevious critique to address: {state.critique}\n"
            self._log(state, f"revising itinerary (revision #{state.revision_count})")
        else:
            self._log(state, "drafting initial itinerary")

        user_prompt = (
            f"Destination: {req.destination}\n"
            f"Duration: {req.duration_days} days\n"
            f"Interests: {', '.join(req.interests)}\n"
            f"Research notes: {state.research_notes}\n"
            f"Attractions available: {', '.join(state.attractions)}\n"
            f"Budget status: {state.budget_notes}\n"
            f"{revision_note}\n"
            "Draft a day-by-day itinerary."
        )
        self.llm.chat(self.system_prompt, user_prompt)  # narrative draft (logged, not required below)

        # Deterministically build the structured day-by-day plan so the
        # output is always well-formed regardless of what the LLM (mock or
        # real) returns in free text — a common and important pattern:
        # use the LLM for judgement/phrasing, use code for structure.
        itinerary = []
        attractions = state.attractions or ["Free walking exploration"]
        for day in range(1, req.duration_days + 1):
            morning = attractions[(day - 1) % len(attractions)]
            afternoon = attractions[day % len(attractions)] if len(attractions) > 1 else "Local neighborhood exploration"
            itinerary.append({
                "day": day,
                "morning": morning,
                "afternoon": afternoon,
                "evening": "Local dinner recommendation within budget",
            })

        state.itinerary = itinerary
        return state
