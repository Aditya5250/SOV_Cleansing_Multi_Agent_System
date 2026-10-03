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
    expose_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
@app.get("/api/health")
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

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)
