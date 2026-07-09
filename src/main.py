"""
CLI demo for the multi-agent trip planner.

Run: python -m src.main
(or edit the request below and re-run)
"""

from src.state import TripRequest
from src.orchestrator import TripPlannerOrchestrator


def print_result(state):
    print("=" * 70)
    print(f"TRIP PLAN: {state.request.destination.title()} "
          f"({state.request.duration_days} days, {state.request.travel_style} style)")
    print("=" * 70)

    print("\n--- Research Notes ---")
    print(state.research_notes)

    print("\n--- Budget ---")
    print(f"Flight: ${state.estimated_flight_cost}")
    print(f"Hotel/night: ${state.estimated_hotel_cost_per_night}")
    print(f"Total estimated cost: ${state.estimated_total_cost}")
    print(f"Within budget (${state.request.budget_total}): {state.within_budget}")
    print(f"Note: {state.budget_notes}")

    print("\n--- Itinerary ---")
    for day in state.itinerary:
        print(f"Day {day['day']}: Morning - {day['morning']} | "
              f"Afternoon - {day['afternoon']} | Evening - {day['evening']}")

    print("\n--- Critic Verdict ---")
    print(state.critique)
    print(f"Revisions needed: {state.revision_count}")

    print("\n--- Agent Trace ---")
    for line in state.trace:
        print(f"  {line}")


def main():
    # Example 1: comfortably within budget
    request_1 = TripRequest(
        destination="Tokyo",
        duration_days=5,
        budget_total=3000,
        interests=["food", "culture", "technology"],
        origin_city="New York",
        travel_style="mid-range",
    )

    # Example 2: intentionally tight budget, to demonstrate the
    # critic-driven revision loop actually triggering
    request_2 = TripRequest(
        destination="Paris",
        duration_days=7,
        budget_total=900,
        interests=["art", "history"],
        origin_city="New York",
        travel_style="luxury",
    )

    orchestrator = TripPlannerOrchestrator()

    print("\n\n############ RUN 1: within-budget trip ############")
    state_1 = orchestrator.run(request_1)
    print_result(state_1)

    print("\n\n############ RUN 2: tight-budget trip (expect revision loop) ############")
    state_2 = orchestrator.run(request_2)
    print_result(state_2)


if __name__ == "__main__":
    main()
