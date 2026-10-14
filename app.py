from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/static/style.css")
def css_static():
    return FileResponse(os.path.join(BASE, "style.css"), media_type="text/css")

@app.get("/static/script.js")
def js_static():
    return FileResponse(os.path.join(BASE, "script.js"), media_type="application/javascript")

# Fix HEAD request that Render does (was giving 405)
@app.head("/")
def home_head():
    return JSONResponse(content=None, status_code=200)

@app.get("/api/health")
@app.get("/health")
def health():
    return {"status": "ok", "message": "MIET AI Assistant Live"}

@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "Hello")
        # Simple response - your original AI logic will go here
        return {
            "answer": f"You asked: '{msg}'\n\nThis is MIET Jammu AI Assistant. I answer from official mietjammu.in website. For now backend is connected successfully!",
            "sources": ["https://mietjammu.in"]
        }
    except Exception as e:
        return {"answer": f"Backend connected! Error: {str(e)}", "sources": []}
