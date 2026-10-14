"""
app.py - Final Fixed Version for Render
Team: Danish Sharma, Kartik Sharma, Dheeraj Thakur
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

app = FastAPI(title="MIET Jammu Chatbot", version="1.0.0")

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
]

def get_file_path(filename):
    # Try root first, then frontend folder
    root_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(root_path):
        return root_path
    frontend_path = os.path.join(BASE_DIR, "frontend", filename)
    if os.path.exists(frontend_path):
        return frontend_path
    return root_path

# --- FIX 1: HEAD request for Render (fixes 405 error) ---
@app.head("/")
def home_head():
    return JSONResponse(content=None, status_code=200)

# --- FIX 2: Serve Frontend correctly ---
@app.get("/")
def serve_index():
    return FileResponse(get_file_path("index.html"))

@app.get("/style.css")
@app.get("/static/style.css")
def serve_css():
    path = get_file_path("style.css")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/css")
    return JSONResponse({"error": "style.css not found"}, status_code=404)

@app.get("/script.js")
@app.get("/static/script.js")
def serve_js():
    path = get_file_path("script.js")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/javascript")
    return JSONResponse({"error": "script.js not found"}, status_code=404)

@app.get("/api/health")
@app.get("/health")
def health():
    try:
        total_chunks = len(database.get_all_chunks
