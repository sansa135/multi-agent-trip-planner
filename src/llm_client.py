"""
LLM client abstraction.

Design goal: every agent talks to this single interface, never to a
provider SDK directly. That means:
  - Swapping providers (Anthropic <-> OpenAI) touches one file
  - The whole multi-agent pipeline is runnable and testable with ZERO API
    key / cost, via the offline MockLLM, and a real LLM can be swapped in
    with one environment variable for actual production use.

Set USE_REAL_LLM=true and ANTHROPIC_API_KEY (or OPENAI_API_KEY) in the
environment to call a real model instead of the deterministic mock.
"""

import os
import json
import requests


class LLMClient:
    """Common interface every agent uses."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class AnthropicLLMClient(LLMClient):
    """Real Claude API client, used when USE_REAL_LLM=true."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return "".join(block["text"] for block in data["content"] if block["type"] == "text")


class MockLLMClient(LLMClient):
    """
    Deterministic, offline stand-in for a real LLM.

    It doesn't call any network API — instead it interpolates the given
    prompts into template responses so the ENTIRE multi-agent pipeline can
    be run, demoed, and unit-tested with no API key and no cost. This is
    also good practice generally: it's what you'd want for fast CI tests
    even in a project that uses a real LLM in production.
    """

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        # Very small "intent router" so different agents get sensibly
        # different canned-but-input-aware answers instead of one generic blob.
        role = self._infer_role(system_prompt)
        if role == "research":
            return self._mock_research(user_prompt)
        elif role == "itinerary":
            return self._mock_itinerary(user_prompt)
        elif role == "critic":
            return self._mock_critique(user_prompt)
        return f"[mock response for prompt: {user_prompt[:80]}...]"

    @staticmethod
    def _infer_role(system_prompt: str) -> str:
        sp = system_prompt.lower()
        if "research" in sp:
            return "research"
        if "itinerary" in sp:
            return "itinerary"
        if "critic" in sp or "review" in sp:
            return "critic"
        return "generic"

    @staticmethod
    def _mock_research(user_prompt: str) -> str:
        return (
            "Based on available information, this destination offers a mix of "
            "cultural landmarks, local cuisine, and outdoor activities. "
            "Best visited outside peak holiday weeks for lower costs. "
            "Public transit is generally reliable for getting between attractions."
        )

    @staticmethod
    def _mock_itinerary(user_prompt: str) -> str:
        return (
            "Day plan drafted: mornings reserved for the top-rated landmark, "
            "afternoons for a mix of one paid attraction and one free/low-cost "
            "activity, evenings for local food recommendations within budget."
        )

    @staticmethod
    def _mock_critique(user_prompt: str) -> str:
        return "APPROVED: itinerary matches stated interests and stays within budget."


def get_llm_client() -> LLMClient:
    """Factory: returns a real client if configured, otherwise the offline mock."""
    if os.environ.get("USE_REAL_LLM", "false").lower() == "true":
        return AnthropicLLMClient()
    return MockLLMClient()
