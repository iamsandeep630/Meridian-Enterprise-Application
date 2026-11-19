"""
Meridian Enterprise Application Backend
Self Help Agent, Confluence RAG, MeshCentral Remote Remediation & Jira Integration
Port: 8001
"""
import collections
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# In-memory recent log buffer for diagnostic monitoring
LOG_BUFFER = collections.deque(maxlen=300)

class LogCapture:
    def __init__(self, stream):
        self.stream = stream
    def write(self, msg):
        if msg and msg.strip():
            LOG_BUFFER.append(msg.strip())
        self.stream.write(msg)
    def flush(self):
        self.stream.flush()

sys.stdout = LogCapture(sys.stdout)
sys.stderr = LogCapture(sys.stderr)

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import STATIC_DIR
from database import init_db
from rag.retriever import HybridRetriever
from routers import agents, auth, chat, enterprise, pages, remote, support


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed data
    init_db()
    # Initialize Hybrid Retriever for Confluence KB
    HybridRetriever.get_instance()
    yield

app = FastAPI(
    title="Meridian Enterprise Application API",
    version="2.0.0",
    description="Enterprise IT & Finance Helpdesk with Self Help Agent, Confluence RAG, MeshCentral & Jira Integration",
    lifespan=lifespan
)

# CORS Middleware - allow Support Dashboard on port 8002 to access chat and resources
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No-Cache headers middleware for static and HTML files
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith((".html", ".js", ".css")) or request.url.path in ["/", "/support"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount Modular Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(support.router)
app.include_router(remote.router)
app.include_router(enterprise.router)
app.include_router(agents.router)
app.include_router(pages.router)

# Mount Static Files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[GLOBAL UNHANDLED EXCEPTION]: {tb}", flush=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": tb, "type": type(exc).__name__}
    )

@app.get("/api/debug/logs")
def get_debug_logs():
    return {"count": len(LOG_BUFFER), "logs": list(LOG_BUFFER)}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Meridian Enterprise Application",
        "port": 8001,
        "agents": ["SelfHelpAgent"]
    }
