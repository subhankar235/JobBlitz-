import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


def get_llm(temperature: float = 0):
    """
    Single shared factory for the LLM client — OpenRouter only.
    Every node calls get_llm() instead of building its own client,
    so model/timeout/retry behavior lives in exactly one place.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://localhost",
            "X-Title": "Job Search AI Agent",
        },
        max_retries=2,   # auto-retries on transient network/rate-limit errors
        timeout=30,      # don't hang forever on a stalled request
    )