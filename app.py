"""
AI-Powered MIET Jammu Website Chatbot
FastAPI backend with automatic MIET knowledge loading.
"""

import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

import database
import rag

load_dotenv()

app = FastAPI(
    title="AI-Powered MIET Jammu Website Chatbot",
    version="1.3.0",
    description="A general-purpose AI assistant for MIET Jammu students."
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

retriever = rag.Retriever()

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


class Source(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    mode: str


SUGGESTED_QUESTIONS = [
    "What programs does MIET Jammu offer?",
    "Explain recursion with a simple example.",
    "How should a 2nd-year B.Tech student build a strong resume?",
    "Tell me about placements at MIET.",
    "What is the difference between AI, ML and Deep Learning?",
    "Help me plan a study schedule for exams."
]


def get_file_path(filename: str):
    root_path = os.path.join(BASE_DIR, filename)

    if os.path.isfile(root_path):
        return root_path

    frontend_path = os.path.join(
        BASE_DIR,
        "frontend",
        filename
    )

    if os.path.isfile(frontend_path):
        return frontend_path

    raise HTTPException(
        status_code=404,
        detail=f"Frontend file not found: {filename}"
    )


@app.on_event("startup")
def load_miet_knowledge():
    """
    Load existing knowledge or scrape the official MIET website
    when the database is empty.
    """

    try:
        database.init_db()

        current_chunks = database.get_all_chunks()

        if not current_chunks:
            print("[startup] MIET knowledge base is empty.")
            print("[startup] Starting MIET website scraper...")

            import scrape_miet

            scrape_miet.scrape()

        retriever.refresh()

        total = len(retriever.chunks)

        print(
            f"[startup] Knowledge base loaded: {total} chunks"
        )

        if total == 0:
            print(
                "[startup] WARNING: No MIET information was collected."
            )

    except Exception as exc:
        print(
            "[startup] Knowledge loading failed:",
            exc.__class__.__name__
        )


@app.head("/")
def home_head():
    return FileResponse(get_file_path("index.html"))


@app.get("/")
def serve_index():
    return FileResponse(get_file_path("index.html"))


@app.get("/style.css")
@app.get("/static/style.css")
def serve_css():
    return FileResponse(
        get_file_path("style.css"),
        media_type="text/css"
    )


@app.get("/script.js")
@app.get("/static/script.js")
def serve_js():
    return FileResponse(
        get_file_path("script.js"),
        media_type="application/javascript"
    )


@app.get("/api/health")
@app.get("/health")
def health():
    try:
        chunks = database.get_all_chunks()
        total = len(chunks)

        configured = bool(rag.OPENAI_API_KEY)

        return {
            "status": "ok" if (configured or total > 0) else "degraded",
            "chunks": total,
            "llm_configured": configured,
            "model": (
                rag.OPENAI_MODEL if configured else None
            ),
            "mode": "llm" if configured else "local",
            "ready": configured or total > 0
        }

    except Exception as exc:
        print(
            "[health] Database error:",
            exc.__class__.__name__
        )

        raise HTTPException(
            status_code=503,
            detail="Database is currently unavailable."
        )


@app.get("/api/suggestions")
def suggestions():
    return {
        "questions": SUGGESTED_QUESTIONS
    }


@app.post(
    "/api/chat",
    response_model=ChatResponse
)
def chat(payload: ChatRequest):
    try:
        result = rag.answer_question(
            payload.question,
            retriever,
            [m.model_dump() for m in payload.history]
        )

        return result

    except Exception as exc:
        print(
            "[chat] Error:",
            exc.__class__.__name__
        )

        raise HTTPException(
            status_code=503,
            detail="The chatbot service is temporarily unavailable."
        )


@app.post("/api/refresh")
def refresh():
    try:
        import scrape_miet

        stored = scrape_miet.scrape()

        retriever.refresh()

        return {
            "status": "refreshed",
            "new_chunks": stored,
            "total_chunks": len(retriever.chunks)
        }

    except Exception as exc:
        print(
            "[refresh] Error:",
            exc.__class__.__name__
        )

        raise HTTPException(
            status_code=503,
            detail="Knowledge base refresh failed."
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True
    )
