"""
app.py - FastAPI backend for the AI-Powered MIET Jammu Website Chatbot.
=======================================================================
BTech Semester Project
Team: Danish Sharma (2025A6R032), Kartik Sharma (2025A6R003),
      Dheeraj Thakur (2025A6R024)

Endpoints
---------
GET  /                -> serves the chat website (frontend/index.html)
GET  /api/health      -> server + knowledge base status
POST /api/chat        -> {"question": "..."} -> grounded answer + sources
POST /api/refresh     -> rebuild retriever after running scrape_miet.py
GET  /api/suggestions -> suggested questions for the UI

Run on Windows:
    python -m venv venv
    venv\\Scripts\\activate
    pip install -r requirements.txt
    copy .env.example .env      (optionally add OPENAI_API_KEY)
    uvicorn app:app --reload
Then open http://127.0.0.1:8000 in a browser.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database
import rag

load_dotenv()

app = FastAPI(
    title="AI-Powered MIET Jammu Website Chatbot",
    description="RAG chatbot over official MIET Jammu website content.",
    version="1.0.0",
)

# CORS: allows the standalone demo page (opened as a file or from another
# port) to talk to this API during development and demonstration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One retriever instance shared by all requests.
retriever = rag.Retriever()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class Source(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    mode: str


SUGGESTED_QUESTIONS = [
    "What programs does MIET Jammu offer?",
    "What is the fee for the AI and ML certification program?",
    "How do admissions work at MIET?",
    "Tell me about placements at MIET.",
    "What sports facilities are on campus?",
    "Any recent notices for new students?",
]


@app.get("/api/health")
def health() -> dict:
    """Simple status endpoint for the UI header badge."""
    try:
        total_chunks = len(database.get_all_chunks())
        return {
            "status": "ok",
            "chunks": total_chunks,
            "llm_configured": bool(rag.OPENAI_API_KEY),
            "model": rag.OPENAI_MODEL if rag.OPENAI_API_KEY else None,
        }
    except Exception as exc:
        return JSONResponse(
            status_code=500, content={"status": "error", "detail": str(exc)}
        )


@app.get("/api/suggestions")
def suggestions() -> dict:
    return {"questions": SUGGESTED_QUESTIONS}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> dict:
    """Main chatbot endpoint: retrieve -> generate -> cite."""
    try:
        return rag.answer_question(req.question, retriever)
    except Exception as exc:
        # Database or unexpected errors must never crash the chat UI.
        print(f"[app] chat error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="The chatbot hit an internal error. Please try again.",
        )


@app.post("/api/refresh")
def refresh() -> dict:
    """Reload the knowledge base (call after running scrape_miet.py)."""
    try:
        retriever.refresh()
        return {"status": "refreshed", "chunks": len(retriever.chunks)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {exc}")


# ----------------------------------------------------------------------
# Frontend (HTML/CSS/vanilla JS in the frontend/ folder)
# ----------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )
