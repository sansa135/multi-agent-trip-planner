"""
Unit tests for the multi-agent trip planner.
Uses only Python's built-in unittest (no pytest needed).

Run: python -m unittest discover tests -v
"""

import unittest

from src.state import TripRequest, TripState
from src.llm_client import MockLLMClient
from src.orchestrator import TripPlannerOrchestrator
from src.agents.research_agent import ResearchAgent
from src.agents.budget_agent import BudgetAgent
from src.tools import lookup_destination_info, search_flight_price, search_hotel_price


class TestTools(unittest.TestCase):
    def test_lookup_known_destination(self):
        info = lookup_destination_info("Tokyo")
        self.assertIn("Senso-ji Temple", info["attractions"])

    def test_lookup_unknown_destination_falls_back(self):
        info = lookup_destination_info("Nowhereland")
        self.assertTrue(len(info["attractions"]) > 0)

    def test_flight_price_is_deterministic(self):
        p1 = search_flight_price("New York", "Tokyo")
        p2 = search_flight_price("New York", "Tokyo")
        self.assertEqual(p1, p2)

    def test_hotel_price_scales_with_travel_style(self):
        budget = search_hotel_price("Tokyo", "budget")
        luxury = search_hotel_price("Tokyo", "luxury")
        self.assertGreater(luxury, budget)


class TestResearchAgent(unittest.TestCase):
    def test_populates_research_notes_and_attractions(self):
        agent = ResearchAgent(MockLLMClient())
        request = TripRequest(destination="Bali", duration_days=4, budget_total=2000, interests=["beach"])
        state = TripState(request=request)

        state = agent.run(state)

        self.assertIsNotNone(state.research_notes)
        self.assertTrue(len(state.attractions) > 0)
        self.assertTrue(any("research_agent" in line for line in state.trace))


class TestBudgetAgent(unittest.TestCase):
    def test_flags_over_budget_trip(self):
        agent = BudgetAgent(MockLLMClient())
        request = TripRequest(
            destination="Paris", duration_days=10, budget_total=50,  # unrealistically tiny on purpose
            interests=["art"], travel_style="luxury",
        )
        state = TripState(request=request)
        state = agent.run(state)

        self.assertFalse(state.within_budget)
        self.assertGreater(state.estimated_total_cost, request.budget_total)

    def test_flags_within_budget_trip(self):
        agent = BudgetAgent(MockLLMClient())
        request = TripRequest(
            destination="Tokyo", duration_days=3, budget_total=100_000,  # unrealistically huge on purpose
            interests=["food"], travel_style="mid-range",
        )
        state = TripState(request=request)
        state = agent.run(state)

        self.assertTrue(state.within_budget)


class TestOrchestratorEndToEnd(unittest.TestCase):
    def setUp(self):
        self.orchestrator = TripPlannerOrchestrator(llm=MockLLMClient())

    def test_full_pipeline_produces_complete_state(self):
        request = TripRequest(destination="Tokyo", duration_days=5, budget_total=3000, interests=["food", "culture"])
        state = self.orchestrator.run(request)

        self.assertIsNotNone(state.research_notes)
        self.assertIsNotNone(state.estimated_total_cost)
        self.assertIsNotNone(state.itinerary)
        self.assertEqual(len(state.itinerary), 5)
        self.assertTrue(state.approved)

    def test_tight_budget_triggers_revision_loop(self):
        request = TripRequest(
            destination="Paris", duration_days=7, budget_total=900,
            interests=["art", "history"], travel_style="luxury",
        )
        state = self.orchestrator.run(request)

        # Should have hit at least one revision, and must still terminate
        # (guaranteed by max_revisions) rather than looping forever.
        self.assertGreater(state.revision_count, 0)
        self.assertTrue(state.approved)
        self.assertLessEqual(state.revision_count, state.max_revisions)

    def test_revision_loop_always_terminates(self):
        # Adversarial case: budget so low it can NEVER be met.
        # This is the critical test — it proves the max_revisions guard
        # actually prevents an infinite loop, not just that it looks fine
        # in a lucky case.
        request = TripRequest(
            destination="Paris", duration_days=14, budget_total=1,
            interests=["art"], travel_style="luxury",
        )
        state = self.orchestrator.run(request)

        self.assertTrue(state.approved)  # force-approved after max_revisions
        self.assertEqual(state.revision_count, state.max_revisions)


if __name__ == "__main__":
    unittest.main()
