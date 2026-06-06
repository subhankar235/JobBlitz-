# JobBlitz

> An autonomous AI agent that finds, filters, and applies to jobs on your behalf — while you sleep.

JobBlitz is an open-source AI agent built with LangChain, GPT-4o, Firecrawl, and Playwright. It searches job portals in real time, reads each listing, decides if it matches your profile, fills the application form, uploads your CV, and sends you a Telegram alert — all automatically.

---

## How it works

```
Tavily Search
     ↓
Find job URLs (Naukri, LinkedIn, Internshala)
     ↓
Firecrawl scrapes each job description
     ↓
GPT-4o checks: does this match my profile?
     ↓
Already applied? → Skip (SQLite check)
     ↓
Playwright: login → fill form → upload CV → submit
     ↓
Telegram alert sent
     ↓
SQLite: log as applied
```

---

## Features

- **Live job search** — Tavily finds fresh listings every morning across multiple portals
- **Smart filtering** — GPT reads each JD and skips jobs that don't match your skills or preferences
- **Auto apply** — Playwright handles login, form filling, CV upload, and submission end to end
- **No duplicates** — SQLite tracks every job seen and applied to across all runs
- **Telegram alerts** — instant notification for every successful application
- **Scheduled runs** — APScheduler runs the full pipeline every morning automatically

---

## Tech stack

| Layer | Tool | Purpose |
|---|---|---|
| Search | Tavily | Find live job listing URLs |
| Scraping | Firecrawl | Read public job description pages |
| Browser | Playwright | Login, fill forms, submit applications |
| Agent brain | LangChain | Orchestrate tools, decide next action |
| LLM | GPT-4o | Filter jobs, tailor answers, reason |
| Storage | SQLite | Track applied jobs, avoid duplicates |
| Alerts | Telegram Bot | Notify on every successful apply |
| Scheduler | APScheduler | Run every morning automatically |

---

## Project structure

```
jobblitz/
├── main.py              # entry point, runs the agent
├── agent.py             # LangChain agent + tool definitions
├── tools/
│   ├── search.py        # Tavily search tool
│   ├── scraper.py       # Firecrawl scrape tool
│   ├── browser.py       # Playwright login + apply tool
│   └── alerter.py       # Telegram notification tool
├── db/
│   └── tracker.py       # SQLite job tracker
├── config.py            # your profile, preferences, target roles
├── .env                 # API keys (never commit this)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourname/jobblitz.git
cd jobblitz
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Set up your `.env`

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 4. Edit your profile in `config.py`

```python
MY_PROFILE = {
    "name": "Rahul Sharma",
    "role": "AI Engineer",
    "skills": ["Python", "LangChain", "RAG", "Fine-tuning", "FastAPI"],
    "experience_years": 2,
    "location": "Bangalore",
    "max_ctc": "12 LPA",
    "cv_path": "resume/rahul_sharma_cv.pdf",
}

JOB_SEARCH_QUERIES = [
    "AI Engineer jobs Bangalore 2025",
    "LLM Engineer fresher jobs India",
    "Python developer Gen AI Bangalore",
]

PORTALS = ["naukri.com", "linkedin.com/jobs", "internshala.com"]
RUN_EVERY_HOURS = 6
```

### 5. Run

```bash
python main.py
```

The agent runs once immediately on start, then every 6 hours automatically.

---

## Environment variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | GPT-4o for filtering and reasoning |
| `TAVILY_API_KEY` | Live job search across portals |
| `FIRECRAWL_API_KEY` | Scrape job description pages |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID for alerts |

---

## Requirements

```
langchain
langchain-openai
langchain-community
firecrawl-py
playwright
tavily-python
python-telegram-bot
apscheduler
python-dotenv
sqlite3
```

---

## Roadmap

- [ ] Phase 1 — Core agent (search + scrape + apply + notify)
- [ ] Phase 2 — Resume tailoring with ChromaDB (match experience to each JD)
- [ ] Phase 3 — Dashboard to view all applications and statuses
- [ ] Phase 4 — Support for more portals (Wellfound, Cutshort, AngelList)
- [ ] Phase 5 — Interview scheduler integration

---

## Important note

Use JobBlitz responsibly. Check each portal's terms of service before running automated applications. Some platforms prohibit automated access. JobBlitz is intended for personal use only.

---

## License

MIT — free to use, modify, and share.
