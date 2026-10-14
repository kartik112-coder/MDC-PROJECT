"""
app.py - Final Fixed Version for Render
Team: Danish Sharma (2025A6R032), Kartik Sharma (2025A6R003), Dheeraj Thakur (2025A6R024)
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

import database
import rag

load_dotenv()

app = FastAPI(
    title="AI-Powered MIET Jammu Website Chatbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

def get_file_path(filename: str) -> str:
    root_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(root_path):
        return root_path
    frontend_path = os.path.join(BASE_DIR, "frontend", filename)
    if os.path.exists(frontend_path):
        return frontend_path
    return root_path

@app.head("/")
def home_head():
    return JSONResponse(content=None, status_code=200)

@app.get("/")
def serve_index():
    return FileResponse(get_file_path("index.html"))

@app.get("/style.css")
@app.get("/static/style.css")
def serve_css():
    path = get_file_path("style.css")
    return FileResponse(path, media_type="text/css")

@app.get("/script.js")
@app.get("/static/script.js")
def serve_js():
    path = get_file_path("script.js")
    return FileResponse(path, media_type="application/javascript")

@app.get("/api/health")
@app.get("/health")
def health():
    try:
        chunks = database.get_all_chunks()
        total = len(chunks)
        return {
            "status": "ok",
            "chunks": total,
            "llm_configured": bool(rag.OPENAI_API_KEY),
            "model": rag.OPENAI_MODEL if rag.OPENAI_API_KEY else None,
        }
    except Exception as exc:
        return {
            "status": "ok",
            "chunks": len(retriever.chunks),
            "detail": str(exc),
        }

@app.get("/api/suggestions")
def suggestions():
    return {"questions": SUGGESTED_QUESTIONS}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: Request):
    try:
        data = await request.json()
        q = data.get("question") or data.get("message") or ""
        q = q.strip()
        if not q:
            raise HTTPException(status_code=400, detail="No question provided")
        return rag.answer_question(q, retriever)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[app] chat error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/refresh")
def refresh():
    try:
        retriever.refresh()
        return {"status": "refreshed", "chunks": len(retriever.chunks)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {exc}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )
