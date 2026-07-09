"""
Orchestrator: the supervisor that coordinates the agent pipeline.

This is a small, explicit state machine — the same core idea LangGraph
formalizes with a graph abstraction, implemented directly here so the
control flow (including the conditional retry loop) is fully visible:

    ResearchAgent -> BudgetAgent -> ItineraryAgent -> CriticAgent
                                          ^                |
                                          |__ (if rejected, retry) __|
                                                            |
                                                     (if approved) -> END

Guarantees termination via `max_revisions` on the state, so a persistently
unhappy CriticAgent can't loop forever.
"""

from src.state import TripState, TripRequest
from src.llm_client import get_llm_client
from src.agents.research_agent import ResearchAgent
from src.agents.budget_agent import BudgetAgent
from src.agents.itinerary_agent import ItineraryAgent
from src.agents.critic_agent import CriticAgent


class TripPlannerOrchestrator:
    def __init__(self, llm=None):
        llm = llm or get_llm_client()
        self.research_agent = ResearchAgent(llm)
        self.budget_agent = BudgetAgent(llm)
        self.itinerary_agent = ItineraryAgent(llm)
        self.critic_agent = CriticAgent(llm)

    def run(self, request: TripRequest) -> TripState:
        state = TripState(request=request)
        state.log(f"orchestrator: starting trip plan for {request.destination}")

        state = self.research_agent.run(state)
        state = self.budget_agent.run(state)

        # Draft -> critique -> (maybe revise) loop
        while True:
            state = self.itinerary_agent.run(state)
            state = self.critic_agent.run(state)
            if state.approved:
                break

        state.log("orchestrator: trip plan finalized")
        return state
