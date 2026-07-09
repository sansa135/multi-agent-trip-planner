"""
Shared state definition passed between agents.

Using a single typed state object (rather than free-form dicts) is what
production agent frameworks like LangGraph do under the hood — it keeps
every agent's inputs/outputs explicit and makes the whole pipeline testable.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TripRequest:
    destination: str
    duration_days: int
    budget_total: float
    interests: list[str]
    origin_city: str = "New York"
    travel_style: str = "mid-range"  # budget | mid-range | luxury


@dataclass
class TripState:
    """The single object passed through the agent pipeline and mutated
    (via returned copies) by each agent as it does its part of the work."""

    request: TripRequest

    # Populated by ResearchAgent
    research_notes: Optional[str] = None
    attractions: list[str] = field(default_factory=list)

    # Populated by BudgetAgent
    estimated_flight_cost: Optional[float] = None
    estimated_hotel_cost_per_night: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    within_budget: Optional[bool] = None
    budget_notes: Optional[str] = None

    # Populated by ItineraryAgent
    itinerary: Optional[list[dict]] = None

    # Populated by CriticAgent
    critique: Optional[str] = None
    approved: bool = False

    # Orchestration bookkeeping
    revision_count: int = 0
    max_revisions: int = 2
    trace: list[str] = field(default_factory=list)

    def log(self, message: str):
        self.trace.append(message)
