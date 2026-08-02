from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import JobSearchState
from graph import nodes as n
from graph import routing as r


def build_graph():
    g = StateGraph(JobSearchState)

    # ---- Register every node (every box in the diagram) ----
    g.add_node("understand_query", n.understand_query)
    g.add_node("ask_clarification", n.ask_clarification)
    g.add_node("dispatch_search", n.dispatch_search)
    g.add_node("search_remoteco", n.search_remoteco_node)
    g.add_node("filter_jobs", n.filter_jobs)
    g.add_node("summarize_jobs", n.summarize_jobs)
    g.add_node("search_another_source", n.search_another_source)
    g.add_node("rank_jobs", n.rank_jobs)
    g.add_node("human_approval", n.human_approval)
    g.add_node("change_filters", n.change_filters)
    g.add_node("generate_resume", n.generate_resume_node)
    g.add_node("review_resume", n.review_resume)
    g.add_node("improve_resume", n.improve_resume_node)
    g.add_node("apply_to_job", n.apply_node)
    g.add_node("save_results", n.save_results)

    # ---- Entry point ----
    g.add_edge(START, "understand_query")

    # ---- Conditional edge #1: Enough Info? ----
    g.add_conditional_edges(
        "understand_query",
        r.route_enough_info,
        {"ask": "ask_clarification", "search": "dispatch_search"},
    )
    g.add_edge("ask_clarification", "understand_query")   # LOOP

    # ---- Fan-out: dispatch_search -> single search branch (Adzuna) ----
    g.add_edge("dispatch_search", "search_remoteco")

    # ---- Fan-in: search branch -> filter_jobs ----
    g.add_edge("search_remoteco", "filter_jobs")

    # ---- Conditional edge #2: Too Many / Few Jobs? ----
    g.add_conditional_edges(
        "filter_jobs",
        r.route_job_count,
        {"many": "summarize_jobs", "few": "search_another_source"},
    )
    g.add_edge("search_another_source", "filter_jobs")     # LOOP (bounded)

    g.add_edge("summarize_jobs", "rank_jobs")
    g.add_edge("rank_jobs", "human_approval")

    # ---- Conditional edge #3: Human Approval? ----
    g.add_conditional_edges(
        "human_approval",
        r.route_human_approval,
        {"approve": "generate_resume", "reject": "change_filters"},
    )
    g.add_edge("change_filters", "filter_jobs")            # LOOP (human-driven)

    g.add_edge("generate_resume", "review_resume")

    # ---- Conditional edge #4: Resume Good? ----
    g.add_conditional_edges(
        "review_resume",
        r.route_resume_quality,
        {"good": "apply_to_job", "improve": "improve_resume"},
    )
    g.add_edge("improve_resume", "review_resume")          # LOOP (bounded)

    # ---- Conditional edge #5: Apply succeeded? ----
    g.add_conditional_edges(
        "apply_to_job",
        r.route_apply_result,
        {"retry": "apply_to_job", "done": "save_results"},
    )

    g.add_edge("save_results", END)

    # Checkpointer is REQUIRED for interrupt() to work — it's what lets
    # the graph pause mid-run and resume later from the exact same point.
    checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)