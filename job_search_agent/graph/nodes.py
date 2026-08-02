from graph.state import JobSearchState
from tools.job_search_tools import SOURCE_FUNCS, apply_to_job, ToolError
from tools.resume_tools import generate_resume, critique_resume, improve_resume
from langgraph.types import interrupt
import json
import time
import os

FEW_JOBS_THRESHOLD = 5


# ────────────────────────────────────────────────────────────
# 1. UNDERSTAND QUERY
# ────────────────────────────────────────────────────────────
def understand_query(state: JobSearchState) -> dict:
    from utils.llm import get_llm
    llm = get_llm(temperature=0)
    prompt = (
        f"Extract job search criteria from this query as JSON with keys "
        f"'role', 'location', 'skills' (list). If a field is unknown, "
        f"set it to null. Query: {state['user_query']}\n"
        f"Also considering any prior clarification: {state.get('clarification_answer')}\n"
        f"Respond with ONLY the JSON object."
    )
    raw = llm.invoke(prompt).content
    try:
        criteria = json.loads(raw)
    except json.JSONDecodeError:
        criteria = {"role": None, "location": None, "skills": []}

    missing = [k for k in ("role", "location") if not criteria.get(k)]

    return {
        "parsed_criteria": criteria,
        "missing_fields": missing,
    }


# ────────────────────────────────────────────────────────────
# 2. ASK CLARIFICATION  (Human-in-the-loop, loop back)
# ────────────────────────────────────────────────────────────
def ask_clarification(state: JobSearchState) -> dict:
    question = (
        f"I still need: {', '.join(state['missing_fields'])}. "
        f"Could you clarify?"
    )
    answer = interrupt({"question": question})
    return {"clarification_answer": answer}


# ────────────────────────────────────────────────────────────
# 3. DISPATCH SEARCH  (fan-out junction — does no real work)
# ────────────────────────────────────────────────────────────
def dispatch_search(state: JobSearchState) -> dict:
    return {}


# ────────────────────────────────────────────────────────────
# 4. THREE PARALLEL SEARCH NODES (fan-out branches)
# ────────────────────────────────────────────────────────────
def search_remoteco_node(state: JobSearchState) -> dict:
    try:
        jobs = SOURCE_FUNCS["remoteco"](state["parsed_criteria"])
        return {"jobs": jobs}
    except ToolError as e:
        return {"jobs": [], "errors": [f"search failed: {e}"]}


# ────────────────────────────────────────────────────────────
# 5. FILTER JOBS
# ────────────────────────────────────────────────────────────
def filter_jobs(state: JobSearchState) -> dict:
    criteria = state["parsed_criteria"]
    role_kw = (criteria.get("role") or "").lower()

    seen = set()
    filtered = []
    for job in state["jobs"]:
        key = (job["title"], job["company"])
        if key in seen:
            continue
        seen.add(key)
        if role_kw and role_kw not in job["title"].lower():
            continue
        filtered.append(job)

    return {"filtered_jobs": filtered}


# ────────────────────────────────────────────────────────────
# 6a. TOO MANY → SUMMARIZE
# ────────────────────────────────────────────────────────────
def summarize_jobs(state: JobSearchState) -> dict:
    top = state["filtered_jobs"][:10]
    return {"filtered_jobs": top}


# ────────────────────────────────────────────────────────────
# 6b. TOO FEW → SEARCH ANOTHER SOURCE (retry loop)
# ────────────────────────────────────────────────────────────
def search_another_source(state: JobSearchState) -> dict:
    round_num = state.get("search_round", 0) + 1
    try:
        extra = SOURCE_FUNCS["remoteco"](state["parsed_criteria"])
        return {"jobs": extra, "search_round": round_num}
    except ToolError as e:
        return {"errors": [f"extra search failed: {e}"], "search_round": round_num}


# ────────────────────────────────────────────────────────────
# 7. RANK JOBS
# ────────────────────────────────────────────────────────────
def rank_jobs(state: JobSearchState) -> dict:
    criteria = state["parsed_criteria"]
    skills = [s.lower() for s in (criteria.get("skills") or [])]

    def score(job):
        text = f"{job['title']} {job['company']}".lower()
        return sum(1 for s in skills if s in text)

    ranked = sorted(state["filtered_jobs"], key=score, reverse=True)
    return {"ranked_jobs": ranked}


# ────────────────────────────────────────────────────────────
# 8. HUMAN APPROVAL  (interrupt)
# ────────────────────────────────────────────────────────────
def human_approval(state: JobSearchState) -> dict:
    payload = {
        "question": "Approve these ranked jobs & current filters? (yes/no)",
        "ranked_jobs": state["ranked_jobs"][:5],
        "criteria": state["parsed_criteria"],
    }
    decision = interrupt(payload)
    return {"human_decision": decision.strip().lower()}


# ────────────────────────────────────────────────────────────
# 8b. REJECTED → CHANGE FILTERS  (interrupt, then loop back)
# ────────────────────────────────────────────────────────────
def change_filters(state: JobSearchState) -> dict:
    note = interrupt({
        "question": "What should change? (e.g. 'widen location', 'different role title')",
        "current_criteria": state["parsed_criteria"],
    })
    updated = dict(state["parsed_criteria"])
    updated["notes"] = note
    return {"parsed_criteria": updated, "human_decision": None}


# ────────────────────────────────────────────────────────────
# 9. GENERATE RESUME
# ────────────────────────────────────────────────────────────
def generate_resume_node(state: JobSearchState) -> dict:
    top_job = state["ranked_jobs"][0]
    try:
        resume = generate_resume(top_job, state["user_background"])
        return {"resume": resume, "resume_attempts": 0}
    except Exception as e:
        return {"errors": [f"resume generation failed: {e}"], "resume": ""}


# ────────────────────────────────────────────────────────────
# 10. REVIEW RESUME
# ────────────────────────────────────────────────────────────
def review_resume(state: JobSearchState) -> dict:
    top_job = state["ranked_jobs"][0]
    attempts = state.get("resume_attempts", 0) + 1
    result = critique_resume(state["resume"], top_job)
    return {
        "resume_good": result["good"],
        "resume_feedback": result["feedback"],
        "resume_attempts": attempts,
    }


# ────────────────────────────────────────────────────────────
# 11. IMPROVE RESUME  (loop back to review)
# ────────────────────────────────────────────────────────────
def improve_resume_node(state: JobSearchState) -> dict:
    top_job = state["ranked_jobs"][0]
    improved = improve_resume(state["resume"], state["resume_feedback"], top_job)
    return {"resume": improved}


# ────────────────────────────────────────────────────────────
# 12. APPLY  (retry loop + graceful degradation)
# ────────────────────────────────────────────────────────────
def apply_node(state: JobSearchState) -> dict:
    top_job = state["ranked_jobs"][0]
    attempts = state.get("apply_attempts", 0) + 1
    try:
        apply_to_job(top_job)
        return {"applied": True, "apply_attempts": attempts}
    except ToolError as e:
        return {
            "applied": False,
            "apply_attempts": attempts,
            "errors": [f"apply attempt {attempts} failed: {e}"],
        }


# ────────────────────────────────────────────────────────────
# 13. SAVE RESULTS
# ────────────────────────────────────────────────────────────
def save_results(state: JobSearchState) -> dict:
    os.makedirs("data/results", exist_ok=True)
    path = f"data/results/run_{int(time.time())}.json"
    with open(path, "w") as f:
        json.dump({
            "query": state["user_query"],
            "criteria": state["parsed_criteria"],
            "ranked_jobs": state["ranked_jobs"],
            "resume": state["resume"],
            "applied": state["applied"],
            "errors": state.get("errors", []),
        }, f, indent=2)
    return {"saved_path": path}