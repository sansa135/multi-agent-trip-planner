"""Base class every specialized agent inherits from."""

from src.llm_client import LLMClient
from src.state import TripState


class BaseAgent:
    name: str = "base_agent"
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, state: TripState) -> TripState:
        raise NotImplementedError

    def _log(self, state: TripState, message: str):
        state.log(f"[{self.name}] {message}")
