from graph.builder import build_graph
from langgraph.types import Command

def run():
    app = build_graph()
    config = {"configurable": {"thread_id": "job-search-session-1"}}

    initial_state = {
        "user_query": input("What job are you looking for? "),
        "user_background": input("Briefly describe your background/skills: "),
        "parsed_criteria": {},
        "missing_fields": [],
        "clarification_answer": None,
        "jobs": [],
        "search_round": 0,
        "filtered_jobs": [],
        "ranked_jobs": [],
        "human_decision": None,
        "filter_feedback": None,
        "resume": None,
        "resume_feedback": None,
        "resume_attempts": 0,
        "applied": False,
        "apply_attempts": 0,
        "resume_good": False,
        "saved_path": None,
        "errors": [],
    }

    result = app.invoke(initial_state, config=config)

    # If the graph paused on an interrupt(), keep resuming until it's done.
    while "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        print("\n--- HUMAN INPUT NEEDED ---")
        print(interrupt_info.get("question", interrupt_info))
        user_reply = input("> ")
        result = app.invoke(Command(resume=user_reply), config=config)

    print("\n--- DONE ---")
    print("Applied:", result["applied"])
    print("Saved to:", result["saved_path"])
    if result.get("errors"):
        print("Errors encountered along the way:", result["errors"])


if __name__ == "__main__":
    run()