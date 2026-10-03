import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.app.api.routes import router as api_router

app = FastAPI(
    title="Agentic SOV Cleansing & Intelligence System",
    description="Automated Property & Casualty Statement of Values standardisation via 4 collaborative AI agents with Human-in-the-Loop review.",
    version="1.0.0"
)

# CORS configuration
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "Agentic SOV Cleansing & Intelligence System",
        "version": "1.0.0",
        "agents": [
            "Agent 1: Sheet Intelligence & Discovery Agent",
            "Agent 2: Schema Mapping Agent",
            "Agent 3: Data Quality & Reasoning Agent",
            "Agent 4: Controlled Transformation Agent"
        ]
    }

# Serve frontend static files if dist exists (e.g. unified Docker container / Hugging Face Spaces)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Request

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/static-assets", StaticFiles(directory=frontend_dist), name="static-assets")

    @app.exception_handler(404)
    async def spa_404_handler(request: Request, exc: Exception):
        if not request.url.path.startswith("/api/"):
            # Check if direct file exists in frontend/dist
            rel_path = request.url.path.lstrip("/")
            file_path = os.path.join(frontend_dist, rel_path)
            if rel_path and os.path.isfile(file_path):
                return FileResponse(file_path)
            index_path = os.path.join(frontend_dist, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    @app.get("/")
    async def serve_index():
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not built"}

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
