# Multi-Agent Trip Planner

A multi-agent system where four specialized agents — Research, Budget,
Itinerary, and Critic — coordinate through a supervising orchestrator to
plan a trip, with a genuine **critique → revision loop**: if the Critic
agent rejects a draft (e.g. it's over budget), the orchestrator routes
control back to the Itinerary agent for a revision, up to a bounded number
of retries.

Built without LangGraph/CrewAI so the orchestration logic — routing,
shared state, and the conditional retry loop — is fully visible in plain
Python rather than hidden behind a framework. Swapping in LangGraph later
would mean re-expressing this same graph, not re-designing it.

## Why this project

Agentic AI is the fastest-growing theme in AI hiring right now — roughly
40% of enterprise apps are expected to embed AI agents by the end of 2026
(up from under 5% in 2024), and the ability to design multi-agent systems
is increasingly called out as a differentiating skill for AI/ML roles.
This project demonstrates the core competencies that signals: shared
state design, agent-to-agent handoff, tool use, and — critically — a
**bounded feedback loop that's guaranteed to terminate**, which is exactly
the kind of reliability engineering that separates a production-ready
agent system from a fragile demo.

## Architecture

```
                 ┌─────────────────┐
   TripRequest → │  ResearchAgent   │  (looks up destination info)
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │   BudgetAgent    │  (estimates flight/hotel/food cost)
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐◄───────┐
                 │  ItineraryAgent  │        │  revise
                 └────────┬─────────┘        │  (max 2x)
                          ▼                  │
                 ┌─────────────────┐         │
                 │   CriticAgent    │ ────────┘
                 └────────┬─────────┘
                          ▼ (approved)
                        RESULT
```

Every agent reads and writes a single shared `TripState` object (see
`src/state.py`) — this is the same core pattern LangGraph formalizes with
its `StateGraph` abstraction.

## Key design decisions (worth highlighting in an interview)

1. **LLM calls are abstracted behind one interface** (`src/llm_client.py`).
   Every agent talks to `LLMClient.chat()`, never to a provider SDK
   directly — swapping Claude for GPT touches one file, not five agents.
2. **The whole pipeline runs and is unit-tested with zero API cost.**
   `MockLLMClient` is a deterministic, input-aware stand-in for a real
   model. Flip `USE_REAL_LLM=true` in `.env` to call actual Claude instead
   — no other code changes needed. This is also just good practice: fast,
   free, deterministic CI tests even for a project that uses a real LLM
   in production.
3. **The LLM is never used for arithmetic.** `BudgetAgent` calculates
   costs in plain Python and only asks the LLM to phrase the human-facing
   summary — a real and important pattern, since letting an LLM "do the
   math" is a common source of silent errors in agent systems.
4. **The retry loop is guaranteed to terminate.** `max_revisions` bounds
   the Critic ↔ Itinerary loop. This is tested explicitly with an
   adversarial case (an impossible $1 budget) to prove the system
   force-approves after the cap rather than looping forever — see
   `test_revision_loop_always_terminates` in the test suite.




