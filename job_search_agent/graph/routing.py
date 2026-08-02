from graph.state import JobSearchState

MAX_SEARCH_ROUNDS = 2
MAX_RESUME_ATTEMPTS = 3
MAX_APPLY_ATTEMPTS = 3
FEW_JOBS_THRESHOLD = 5


def route_enough_info(state: JobSearchState) -> str:
    return "ask" if state["missing_fields"] else "search"


def route_job_count(state: JobSearchState) -> str:
    if len(state["filtered_jobs"]) >= FEW_JOBS_THRESHOLD:
        return "many"
    if state.get("search_round", 0) >= MAX_SEARCH_ROUNDS:
        # Safety valve: stop looping even if still "few" — never hang forever.
        return "many"
    return "few"


def route_human_approval(state: JobSearchState) -> str:
    return "approve" if state.get("human_decision") == "yes" else "reject"


def route_resume_quality(state: JobSearchState) -> str:
    if state.get("resume_good"):
        return "good"
    if state.get("resume_attempts", 0) >= MAX_RESUME_ATTEMPTS:
        return "good"  # force forward with best-effort resume
    return "improve"


def route_apply_result(state: JobSearchState) -> str:
    if state.get("applied"):
        return "done"
    if state.get("apply_attempts", 0) >= MAX_APPLY_ATTEMPTS:
        return "done"  # give up gracefully, don't loop forever
    return "retry"