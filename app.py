from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import os

app = FastAPI(title="MIET Chatbot")

# --- Models ---
class Source(BaseModel):
    text: str
    source: str

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    mode: str

SUGGESTED_QUESTIONS = [
    "What programs does MIET Jammu offer?",
    "What is the fee for the AI and ML certification program?",
    "How do admissions work at MIET?",
    "Tell me about placements at MIET.",
    "What sports facilities are on campus?",
    "Any recent notices for new students?",
]

# --- FRONTEND ROUTES - This fixes Not Found ---
@app.get("/")
def home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"detail": "index.html not found in root"}

@app.get("/style.css")
def css():
    return FileResponse("style.css")

@app.get("/script.js")
def js():
    return FileResponse("script.js")

# --- API ROUTES ---
@app.get("/api/health")
def health() -> dict:
    """Simple status endpoint for the UI header badge"""
    return {"status": "ok", "service": "MIET Chatbot"}

@app.get("/api/suggestions")
def suggestions():
    return {"suggestions": SUGGESTED_QUESTIONS}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer = f"Thanks for asking: '{req.question}'. Your backend is now connected! Integrate your RAG logic here."
    return ChatResponse(
        answer=answer,
        sources=[Source(text="MIET official info", source="miet jammu")],
        mode="live"
    )
