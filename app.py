
"""
FastAPI backend for the MIET Jammu AI Chatbot.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

import database
import rag


app = FastAPI(
    title="AI-Powered MIET Jammu Website Chatbot",
    version="1.1.0",
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


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

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
    "What is the fee for the AI and ML certification program?",
    "How do admissions work at MIET?",
    "Tell me about placements at MIET.",
    "What sports facilities are on campus?",
    "Any recent notices for new students?",
]


def get_file_path(filename: str) -> str:
    root_path = os.path.join(BASE_DIR, filename)

    if os.path.isfile(root_path):
        return root_path

    frontend_path = os.path.join(BASE_DIR, "frontend", filename)

    if os.path.isfile(frontend_path):
        return frontend_path

    raise HTTPException(
        status_code=404,
        detail=f"Frontend file not found: {filename}",
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
        media_type="text/css",
    )


@app.get("/script.js")
@app.get("/static/script.js")
def serve_js():
    return FileResponse(
        get_file_path("script.js"),
        media_type="application/javascript",
    )


@app.get("/api/health")
@app.get("/health")
def health():
    try:
        chunks = database.get_all_chunks()
        total = len(chunks)

        configured = bool(rag.OPENAI_API_KEY)

        return {
            "status": (
                "ok" if configured and total > 0
                else "degraded"
            ),
            "chunks": total,
            "llm_configured": configured,
            "model": rag.OPENAI_MODEL if configured else None,
            "ready": configured and total > 0,
        }

    except Exception:
        print("[app] Database health check failed.")

        raise HTTPException(
            status_code=503,
            detail="The database is currently unavailable.",
        )


@app.get("/api/suggestions")
def suggestions():
    return {
        "questions": SUGGESTED_QUESTIONS
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):

    if not rag.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured.",
        )

    try:
        return rag.answer_question(
            payload.question,
            retriever,
        )

    except Exception as exc:
        print(
            f"[app] Chat service error: {exc.__class__.__name__}"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is temporarily unavailable. "
                "Please try again later."
            ),
        )


@app.post("/api/refresh")
def refresh():
    try:
        retriever.refresh()

        return {
            "status": "refreshed",
            "chunks": len(retriever.chunks),
        }

    except Exception as exc:
        print(
            f"[app] Refresh error: {exc.__class__.__name__}"
        )

        raise HTTPException(
            status_code=503,
            detail="Knowledge base refresh failed.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )
