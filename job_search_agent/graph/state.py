from typing import TypedDict, Optional, Annotated
import operator


class JobSearchState(TypedDict):
    # ---- Input ----
    user_query: str
    user_background: str            # candidate's background text, given at start

    # ---- Understand Query ----
    parsed_criteria: dict
    missing_fields: list[str]
    clarification_answer: Optional[str]

    # ---- Search Jobs (fan-out / fan-in) ----
    # operator.add: when multiple nodes return {"jobs": [...]} in the SAME
    # superstep (parallel branches), LangGraph concatenates the lists instead
    # of overwriting. This is what makes fan-in work.
    jobs: Annotated[list[dict], operator.add]
    search_round: int

    # ---- Filter / Summarize ----
    filtered_jobs: list[dict]

    # ---- Rank ----
    ranked_jobs: list[dict]

    # ---- Human Approval (filters) ----
    human_decision: Optional[str]   # "approve" | "reject"
    filter_feedback: Optional[str]

    # ---- Resume ----
    resume: Optional[str]
    resume_feedback: Optional[str]
    resume_attempts: int
    resume_good: bool               # result of the automated resume critique

    # ---- Apply / Save ----
    applied: bool
    apply_attempts: int             # retry counter for the Apply step
    saved_path: Optional[str]

    # ---- Error recovery ----
    # Also accumulates — every failing node appends its own error
    # instead of wiping out errors from earlier nodes.
    errors: Annotated[list[str], operator.add]