from utils.llm import get_llm


def generate_resume(job: dict, user_background: str) -> str:
    llm = get_llm(temperature=0.4)
    prompt = (
        f"Write a concise, tailored one-page resume summary "
        f"for this job:\nTitle: {job['title']}\nCompany: {job['company']}\n\n"
        f"Candidate background:\n{user_background}\n\n"
        f"Output only the resume text."
    )
    response = llm.invoke(prompt)
    return response.content


def critique_resume(resume: str, job: dict) -> dict:
    """
    Returns {"good": bool, "feedback": str}
    Acts as our automated 'Resume Good?' judge.
    """
    llm = get_llm(temperature=0)
    prompt = (
        f"Judge if this resume is well-tailored for the job title "
        f"'{job['title']}' at '{job['company']}'.\n\n"
        f"Resume:\n{resume}\n\n"
        f"Reply in EXACTLY this format:\n"
        f"VERDICT: good OR VERDICT: needs_work\n"
        f"FEEDBACK: <one sentence>"
    )
    response = llm.invoke(prompt).content
    good = "verdict: good" in response.lower()
    feedback_line = next((l for l in response.splitlines() if l.lower().startswith("feedback:")), "")
    feedback = feedback_line.split(":", 1)[-1].strip() if feedback_line else ""
    return {"good": good, "feedback": feedback}


def improve_resume(resume: str, feedback: str, job: dict) -> str:
    llm = get_llm(temperature=0.4)
    prompt = (
        f"Improve this resume based on the feedback.\n\n"
        f"Job: {job['title']} at {job['company']}\n"
        f"Current resume:\n{resume}\n\n"
        f"Feedback to address:\n{feedback}\n\n"
        f"Output only the improved resume text."
    )
    return llm.invoke(prompt).content