# 🧭 Job Search AI Agent (LangGraph)

An autonomous job-search agent that understands a natural language query, searches real job APIs in parallel, filters/ranks results, pauses for human approval, tailors a resume, retries on failure, and applies — all orchestrated as a **LangGraph** state machine.

Built as a teaching project to demonstrate every core LangGraph concept in one coherent, working agent: conditional edges, loops/retries, fan-out/fan-in parallelism, human-in-the-loop interrupts, tool calling, and error recovery.

---

## 🗺️ Architecture

```
User Query
    │
    ▼
Understand Query
    │
    ▼
Enough Info? ──No──► Ask Clarification ──┐
    │Yes                                  │ (loops back)
    ▼                                     │
Search Jobs (fan-out: Indeed│LinkedIn│Adzuna, parallel) ◄┘
    │ (fan-in)
    ▼
Filter Jobs
    │
Too Many/Few? ──Few──► Search Another Source ──┐ (bounded loop)
    │Many                                        │
    ▼◄───────────────────────────────────────────┘
Summarize ──► Rank Jobs
                  │
          Human Approval? ──Reject──► Change Filters ──┐ (loops back to Filter Jobs)
                  │Approve                               │
                  ▼◄──────────────────────────────────────┘
          Generate Resume
                  │
          Resume Good? ──No──► Improve Resume ──┐ (bounded loop)
                  │Yes                            │
                  ▼◄───────────────────────────────┘
          Apply to Job ──Fail──► retry (bounded loop)
                  │Success/give up
                  ▼
          Save Results ──► END
```

---

## ⚙️ Core LangGraph Concepts Demonstrated

| Concept | Where |
|---|---|
| **Conditional edges** | `route_enough_info`, `route_job_count`, `route_human_approval`, `route_resume_quality`, `route_apply_result` |
| **Loops & bounded retries** | Search retry (`search_round`), resume retry (`resume_attempts`), apply retry (`apply_attempts`) — every loop has a state-tracked counter checked by its routing function |
| **Fan-out / fan-in (parallel execution)** | `dispatch_search` → 3 parallel nodes (`search_indeed_node`, `search_linkedin_node`, `search_remoteco_node`) → merge into `filter_jobs` via `Annotated[list, operator.add]` on the `jobs` field |
| **Human-in-the-loop** | `ask_clarification`, `human_approval`, `change_filters` — all use `interrupt()`, pausing the graph and resuming via `Command(resume=...)` |
| **State updates** | Every node returns only the keys it changes; LangGraph merges them into one shared `JobSearchState` |
| **Tool calling** | `tools/job_search_tools.py` (JSearch + Adzuna APIs), `tools/resume_tools.py` (LLM-based resume generation/critique) |
| **Error recovery** | Every tool call is wrapped in `try/except ToolError`, logged to the accumulating `errors` field, and never crashes the graph — failing branches just contribute empty results |

---

## 📁 Folder Structure

```
job_search_agent/
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py
│
├── graph/
│   ├── __init__.py
│   ├── state.py        # Shared schema every node reads/writes
│   ├── nodes.py         # One function per box in the diagram
│   ├── routing.py       # One function per diamond in the diagram
│   └── builder.py       # Wires nodes + routing into the compiled graph
│
├── tools/
│   ├── __init__.py
│   ├── job_search_tools.py   # JSearch (Indeed/LinkedIn) + Adzuna API calls
│   └── resume_tools.py        # LLM-based resume generation/critique
│
├── utils/
│   ├── __init__.py
│   └── llm.py           # Single OpenRouter client factory
│
└── data/
    └── results/          # Saved JSON output per run (.gitkeep tracked, files ignored)
```

---

## 🔑 Prerequisites & API Keys

You need three free-tier accounts:

| Service | Used for | Get a key |
|---|---|---|
| **OpenRouter** | All LLM calls (query parsing, resume writing/critique, ranking logic) | [openrouter.ai](https://openrouter.ai) |
| **RapidAPI (JSearch)** | Indeed + LinkedIn job listings | [rapidapi.com](https://rapidapi.com) → search "JSearch" |
| **Adzuna** | Independent third job-search source | [developer.adzuna.com](https://developer.adzuna.com) |

---

## 🚀 Setup

```bash
# 1. Clone / enter the project
cd job_search_agent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then edit .env and paste in your real keys

# 5. Ensure the output folder exists
mkdir -p data/results
touch data/results/.gitkeep
```

### `.env` contents required

```env
OPENROUTER_API_KEY=your-openrouter-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

RAPIDAPI_KEY=your-rapidapi-key-here

ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
ADZUNA_COUNTRY=us
```

---

## ▶️ Running the Agent

```bash
python main.py
```

You'll be prompted for:
1. **Job you're looking for** (e.g. `"backend engineer, remote"`)
2. **A brief background/skills summary** (used to tailor the resume)

The agent will then run autonomously — searching, filtering, ranking — and will **pause twice** for your input in the terminal:

- Once if your query is missing details (role/location)
- Once to approve the ranked job shortlist before it writes a resume and applies

Example interaction:

```
What job are you looking for? backend engineer
Briefly describe your background/skills: 5 years Python, Django, AWS, Postgres

--- HUMAN INPUT NEEDED ---
I still need: location. Could you clarify?
> remote, US only

--- HUMAN INPUT NEEDED ---
Approve these ranked jobs & current filters? (yes/no)
[... top 5 jobs shown ...]
> yes

--- DONE ---
Applied: True
Saved to: data/results/run_1735689234.json
```

---

## 📄 Output

Every completed run writes a JSON file to `data/results/`:

```json
{
  "query": "backend engineer",
  "criteria": {"role": "backend engineer", "location": "remote, US only", "skills": [...]},
  "ranked_jobs": [...],
  "resume": "...",
  "applied": true,
  "errors": []
}
```

The `errors` array is never omitted — even successful runs show it (empty if nothing failed), so you always have a clear audit trail of what the agent tried and any transient failures it recovered from along the way.

---

## 🛠️ Extending This Project

| Want to... | Change only this |
|---|---|
| Add a 4th job source | `tools/job_search_tools.py` + add one node in `nodes.py` + wire 2 edges in `builder.py` |
| Swap LLM provider/model | `.env` (`OPENROUTER_MODEL`) — no code changes |
| Make checkpoints survive a restart | `graph/builder.py`: swap `MemorySaver()` → `SqliteSaver.from_conn_string(...)` |
| Change retry limits | `graph/routing.py`: edit `MAX_SEARCH_ROUNDS`, `MAX_RESUME_ATTEMPTS`, `MAX_APPLY_ATTEMPTS`, `FEW_JOBS_THRESHOLD` |
| Real application submission | `tools/job_search_tools.py`: replace simulated `apply_to_job` with browser automation (e.g. Playwright) against `job["url"]` |

---

## ⚠️ Known Limitations

- `apply_to_job` is **simulated** — no public API exists for auto-submitting job applications; a real implementation would need browser automation or manual handoff.
- `MemorySaver` checkpoints live only in RAM — killing the process mid-`interrupt()` loses that paused state (see extension table above for the fix).
- Free-tier API quotas (JSearch, Adzuna) are limited — repeated test runs during development can exhaust them quickly; consider caching results locally while iterating.

---

## 📚 Recommended Reading Order (if learning LangGraph from this repo)

1. `graph/state.py` — the shared contract every node depends on
2. `graph/nodes.py` — the actual work, one function per diagram box
3. `graph/routing.py` — the branching decisions, one function per diagram diamond
4. `graph/builder.py` — where the diagram becomes an actual compiled graph
5. `main.py` — how a run is invoked, and how `interrupt()`/`Command(resume=...)` pause and continue execution