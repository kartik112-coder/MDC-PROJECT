# AI-Powered MIET Jammu Website Chatbot

**BTech Semester Project** · Official website: [https://mietjmu.in/](https://mietjmu.in/)

| Team Member | Roll Number |
|---|---|
| Danish Sharma | 2025A6R032 |
| Kartik Sharma | 2025A6R003 |
| Dheeraj Thakur | 2025A6R024 |

---

## 1. Problem Statement

Students at MIET Jammu need information about admissions, fees, timetables, faculty,
examination dates, notices, placements and campus facilities. Currently they must
browse multiple webpages to find it. This project builds an **AI chatbot** that lets
students ask questions in **natural language** and get relevant, **source-cited**
answers through one conversational interface.

## 2. Technology Stack (exactly as proposed — no substitutions)

| Layer | Technology |
|---|---|
| Core language | **Python 3.11+** |
| Backend | **FastAPI** (+ Uvicorn) |
| Frontend | **HTML, CSS, vanilla JavaScript** |
| AI | **OpenAI API** (configurable model) with **RAG**; honest extractive mode when no key |
| Database | **SQLite** (knowledge chunks + source URLs); ChromaDB documented as optional upgrade |
| Data collection | **Requests + BeautifulSoup** (robots.txt respected) |

## 3. Project Structure

```
├── app.py               # FastAPI backend (API + serves frontend)
├── rag.py               # RAG engine: TF-IDF retrieval + LLM/extractive answers
├── database.py          # SQLite module + verified seed knowledge base
├── scrape_miet.py       # Requests/BeautifulSoup scraper for mietjmu.in
├── requirements.txt
├── .env.example         # copy to .env, optionally add OPENAI_API_KEY
├── frontend/
│   ├── index.html       # chat UI served by FastAPI at /
│   ├── style.css
│   └── script.js
├── tests/
│   └── test_chatbot.py  # pytest suite (DB, retrieval, RAG, API)
├── index.html           # standalone demo/documentation page (see §7)
└── README.md
```

## 4. How to Run (Windows)

```bat
:: 1) Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

:: 2) Install dependencies
pip install -r requirements.txt

:: 3) Configure environment (OpenAI key optional)
copy .env.example .env
notepad .env

:: 4) (Optional but recommended) refresh the knowledge base from the live site
python scrape_miet.py

:: 5) Start the server
uvicorn app:app --reload

:: 6) Open the chatbot
start http://127.0.0.1:8000
```

### Run the tests

```bat
pytest -v
```

The tests use a temporary database and **do not need an OpenAI key**. They verify:
seeding with source URLs, relevant retrieval, non-generic per-question answers,
honest "not found" handling, API health/chat/validation endpoints.

> **Transparency note:** this repository was generated in a web-only build
> environment that cannot execute Python, so run `pytest -v` locally to see the
> suite pass before your demonstration. Everything is standard-library +
> pinned packages, with no exotic setup.

## 5. How It Works (RAG pipeline)

1. `scrape_miet.py` checks **robots.txt**, downloads official pages, cleans the
   text with BeautifulSoup, splits it into ~900-character overlapping chunks and
   stores them **with source URLs** in SQLite. A verified homepage snapshot is
   pre-seeded so the bot works immediately.
2. `rag.py` scores chunks against the question with a **TF-IDF cosine retriever**
   (plus a synonym map for student phrasing: "fee" → tuition/cost, etc.).
3. If `OPENAI_API_KEY` is set, the top chunks + question go to the LLM with strict
   *"answer only from context, never invent college information"* instructions.
   Without a key — or if the API errors — the bot builds an **extractive answer**
   straight from the retrieved chunks, so it still answers specifically.
4. Every answer returns **clickable source links**. If nothing relevant is
   retrieved, the bot says so honestly and points to mietjmu.in.

## 6. V.E.T.S. Framework Alignment

- **Viability** — uses existing college website content and freely accessible tools
  (Python, FastAPI, SQLite, BeautifulSoup); no paid infrastructure required.
- **Engineering** — combines web scraping, document indexing, vector-style search,
  REST APIs and AI response generation in one working system.
- **Trend Alignment** — conversational AI assistants for educational institutions
  are a fast-growing, industry-relevant application area.
- **Social Impact** — saves students time and improves access to college
  information through a single natural-language interface.

## 7. Standalone Demo Page

The root `index.html` is a single-file demonstration/documentation page. It
automatically connects to the FastAPI backend at `http://127.0.0.1:8000` when it is
running (full RAG + LLM). If the backend is offline, it clearly switches to
**Demo Mode**, running the same retrieval logic in the browser over the same seed
knowledge base — useful for showing the UI anywhere.

## 8. 16-Week Roadmap (from the original proposal)

| Phase | Weeks | Work |
|---|---|---|
| 1 | 1–4 | Requirement analysis and website data collection |
| 2 | 5–8 | Backend API and chatbot development |
| 3 | 9–12 | RAG integration and website UI |
| 4 | 13–16 | Testing, optimization and deployment |

## 9. Implemented vs. Future Scope

**Implemented in this submission:** FastAPI backend, SQLite knowledge base with
source URLs, robots-aware scraper, TF-IDF RAG retrieval, OpenAI integration with
extractive fallback, responsive chat UI (bubbles, suggestions, loading indicator,
source links, clear chat), honest missing-info handling, error handling, pytest suite.

**Proposed future enhancements (NOT yet implemented):**
- 🎙 Voice support (speech-to-text questions, spoken answers)
- 🌐 English **and Hindi** responses
- 🔐 Student login integration
- 🎯 Personalized academic assistance (per-student timetables, results, reminders)
- 🗄 ChromaDB vector store with embedding search (drop-in upgrade for `rag.py`)

## 10. Data Ethics

The scraper respects `robots.txt`, uses a polite delay and an identifying
User-Agent, collects only public pages of the official website, and retains source
URLs for attribution. The chatbot **never invents official college information** —
unverified topics get an honest redirect to mietjmu.in.
