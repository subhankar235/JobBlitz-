# 🧭 Job Search AI Agent (LangGraph)

An autonomous agent that finds and applies to jobs for you — end to end, with a human checking in only at the moments that matter.

You tell it what job you want and a bit about your background. It takes it from there: understands your request, searches multiple job boards at once, filters and ranks the results, checks in with you before moving forward, writes a tailored resume, and submits the application — automatically retrying and recovering when something fails along the way.

---

## 🎯 What It Actually Does

1. **Understands your request** — takes a plain-English query like *"backend engineer, remote"* and figures out the role, location, and skills you care about. If something's missing, it asks you instead of guessing.

2. **Searches multiple job sources at once** — queries Indeed, LinkedIn, and Adzuna in parallel rather than one after another, so you get a broader set of results faster.

3. **Filters and ranks the results** — narrows the list down to jobs that actually fit, and if too few come back, it automatically goes and searches another source before giving up.

4. **Asks for your approval** — before it does anything with your resume, it shows you the shortlisted jobs and waits for a yes/no. Say no, and it adjusts the filters and tries again.

5. **Writes and improves a tailored resume** — generates a resume aimed at the specific job, critiques its own output, and rewrites it if it's not good enough — up to a set number of attempts.

6. **Applies to the job** — submits the application, and if it fails, retries automatically within a limit before giving up gracefully.

7. **Saves everything** — every run is logged to a JSON file with the query, criteria used, ranked jobs, final resume, whether the application succeeded, and any errors it recovered from along the way — so you always have a clear record of what it did.

---

## 🙋 Where You Come In

The agent runs mostly on its own, but pauses for your input at two points:

- **If your query is unclear** — it'll ask you to clarify (e.g. "I still need: location").
- **Before applying** — it shows you the ranked shortlist and waits for your approval before writing a resume and applying.

Everything else — searching, filtering, ranking, retrying on failure — happens without you needing to step in.

---

## 🔑 What You Need to Run It

Three free-tier accounts, each powering a different part of the pipeline:

| Service | What it's used for |
|---|---|
| **RapidAPI (JSearch)** | Pulling job listings from Indeed and LinkedIn |
| **Adzuna** | A third, independent source of job listings |

---

## ▶️ Running It

```bash
python main.py
```

You'll be asked two things up front — the job you're looking for, and a quick summary of your background/skills — and then the agent takes over, pausing only when it needs your input.

Example:

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




---

## 🛠️ Making It Your Own

| Want to... | What to change |
|---|---|
| Add another job source | Hook it into the search step and the tools it calls |
| Use a different LLM | Just change the model in your `.env` — no code changes needed |
| Make paused runs survive a restart | Swap the in-memory checkpoint for a persistent one (e.g. SQLite) |
| Change how many times it retries | Adjust the retry/attempt limits in the routing logic |
| Actually submit applications | Replace the simulated apply step with real browser automation |
