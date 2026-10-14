from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()
BASE = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    return FileResponse(os.path.join(BASE, "index.html"))

@app.get("/style.css")
def css():
    return FileResponse(os.path.join(BASE, "style.css"), media_type="text/css")

@app.get("/script.js")
def js():
    return FileResponse(os.path.join(BASE, "script.js"), media_type="application/javascript")

@app.get("/health")
def health():
    return {"status": "live", "url": "https://mdc-project.onrender.com"}

@app.post("/api/chat")
async def chat(req: dict):
    return {"answer": "MIET Jammu AI Assistant is live!", "sources": ["mietjammu.in"]}
