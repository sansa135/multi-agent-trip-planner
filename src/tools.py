"""
Mock external tools.

In a production system these would call real APIs (Amadeus/Skyscanner for
flights, Google Places for attractions, a hotel-pricing API, etc). Here
they're deterministic simulations so the agents that call them are fully
testable offline — but they're written behind the same function signature
a real API wrapper would use, so swapping in a real integration later means
rewriting the body of these functions, not the agents that call them.
"""

import hashlib


def _seeded_value(seed_str: str, low: float, high: float) -> float:
    """Deterministic pseudo-random value in [low, high], seeded by a string,
    so the same destination always returns the same mock price/info."""
    h = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    fraction = (h % 10_000) / 10_000
    return round(low + fraction * (high - low), 2)


DESTINATION_DB = {
    "tokyo": {
        "attractions": ["Senso-ji Temple", "Shibuya Crossing", "teamLab Planets", "Tsukiji Outer Market"],
        "avg_daily_food_cost": 35,
        "currency": "USD-equivalent",
    },
    "paris": {
        "attractions": ["Eiffel Tower", "Louvre Museum", "Montmartre", "Seine River Cruise"],
        "avg_daily_food_cost": 45,
        "currency": "USD-equivalent",
    },
    "bali": {
        "attractions": ["Uluwatu Temple", "Tegallalang Rice Terraces", "Ubud Monkey Forest", "Seminyak Beach"],
        "avg_daily_food_cost": 20,
        "currency": "USD-equivalent",
    },
}

DEFAULT_DESTINATION = {
    "attractions": ["Old Town district", "Central Museum", "Main City Park", "Local Market Square"],
    "avg_daily_food_cost": 30,
    "currency": "USD-equivalent",
}


def lookup_destination_info(destination: str) -> dict:
    """Simulates a Google Places / travel-guide API lookup."""
    return DESTINATION_DB.get(destination.strip().lower(), DEFAULT_DESTINATION)


def search_flight_price(origin: str, destination: str) -> float:
    """Simulates a flight-search API (e.g. Amadeus) returning a round-trip price."""
    return _seeded_value(f"flight:{origin.lower()}:{destination.lower()}", 280, 1400)


def search_hotel_price(destination: str, travel_style: str) -> float:
    """Simulates a hotel-pricing API returning a nightly rate."""
    style_multiplier = {"budget": 0.55, "mid-range": 1.0, "luxury": 2.6}.get(travel_style, 1.0)
    base = _seeded_value(f"hotel:{destination.lower()}", 60, 180)
    return round(base * style_multiplier, 2)
