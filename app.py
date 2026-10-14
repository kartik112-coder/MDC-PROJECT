from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI()

# Get current folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def home():
    file_path = os.path.join(BASE_DIR, "index.html")
    return FileResponse(file_path)

@app.get("/style.css")
def css():
    file_path = os.path.join(BASE_DIR, "style.css")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/css")
    return JSONResponse({"error": "style.css not found in root"}, status_code=404)

@app.get("/script.js")
def js():
    file_path = os.path.join(BASE_DIR, "script.js")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/javascript")
    return JSONResponse({"error": "script.js not found in root"}, status_code=404)

@app.get("/api/health")
def health():
    return {"status": "ok", "files": os.listdir(BASE_DIR)}

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("message", "")
    return {"answer": f"MIET Assistant received: {msg}. Your beautiful UI is working!", "sources": ["mietjammu.in"]}
