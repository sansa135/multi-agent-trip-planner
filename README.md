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

## Project structure

```
multi-agent-trip-planner/
├── src/
│   ├── state.py              # shared TripRequest / TripState schema
│   ├── llm_client.py          # LLM abstraction: real Claude API or offline mock
│   ├── tools.py                # mock external tools (flights, hotels, destination info)
│   ├── orchestrator.py         # supervisor: routes agents, runs the revision loop
│   ├── main.py                  # CLI demo runner
│   └── agents/
│       ├── research_agent.py
│       ├── budget_agent.py
│       ├── itinerary_agent.py
│       └── critic_agent.py
├── tests/
│   └── test_orchestrator.py    # 10 unit tests incl. loop-termination proof
├── examples/
│   └── sample_run_output.txt   # real captured output from a live run
├── requirements.txt
├── .env.example
└── README.md
```

## How to run

```bash
pip install -r requirements.txt

# Runs entirely offline with the mock LLM — no API key needed
python -m src.main
```

Sample output (real, captured from an actual run — see
`examples/sample_run_output.txt` for the full transcript):

```
############ RUN 2: tight-budget trip (expect revision loop) ############
TRIP PLAN: Paris (7 days, luxury style)

--- Budget ---
Total estimated cost: $2440.0
Within budget ($900): False

--- Critic Verdict ---
APPROVED with budget caveat: over budget after max revisions;
flagged for traveler to adjust dates/style.
Revisions needed: 2

--- Agent Trace ---
  orchestrator: starting trip plan for Paris
  [research_agent] looked up destination data for 'Paris'
  [budget_agent] flight=$979.66, hotel/night=$178.62, est. total=$2440.00 vs budget=$900
  [itinerary_agent] drafting initial itinerary
  [critic_agent] itinerary rejected: Trip is $1540.00 over budget...
  [itinerary_agent] revising itinerary (revision #1)
  [critic_agent] itinerary rejected: Trip is $1540.00 over budget...
  [itinerary_agent] revising itinerary (revision #2)
  [critic_agent] itinerary approved
  orchestrator: trip plan finalized
```

### Run the tests
```bash
python -m unittest discover tests -v
```
10/10 tests pass, including an adversarial test with an impossible ($1)
budget that proves the revision loop terminates rather than hanging.

### Use a real LLM instead of the mock
```bash
cp .env.example .env
# edit .env: set USE_REAL_LLM=true and add your ANTHROPIC_API_KEY
python -m src.main
```

## Possible extensions
- Add a real tool call (e.g. a live web search) to `ResearchAgent` instead of the mock destination DB
- Add a "human-in-the-loop" checkpoint before finalizing bookings
- Swap the custom orchestrator for LangGraph to compare tradeoffs directly
- Add parallel agent execution (Research + Budget can actually run concurrently, since neither depends on the other's output)
- Expose the orchestrator as a FastAPI endpoint (same pattern as a typical agent-as-a-service deployment)
