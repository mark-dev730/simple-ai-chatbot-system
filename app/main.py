from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
from app.backend.core.config import get_db, test_connection
from app.backend.database.initialized_db import User, OllamaModel
from app.backend.services.ollama_service import ollama_service
import uvicorn

# Import routers
from app.backend.api import auth, chat, sessions, admin, rag

app = FastAPI(
    title="McBOT",
    description="Manufacturing Chatbot with RAG - Local Ollama AI with Oracle database backend",
    version="1.0.0"
)

# CORS middleware - restrict origins for security
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],  # Restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(admin.router)
app.include_router(rag.router)

# Static files and SPA fallback
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    # Serve static files
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
    
    # Serve index.html for all other routes (SPA)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If path starts with /api, let FastAPI handle it
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Otherwise serve index.html
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")

@app.on_event("startup")
async def startup_event():
    """Test database connection and Ollama on startup"""
    print("Starting McBOT (Manufacturing Chatbot)...")
    print("=" * 50)
    
    # Test database
    if test_connection():
        print("✓ Database connection verified")
    else:
        print("✗ Database connection failed")
    
    # Test Ollama
    ollama_connected = await ollama_service.check_connection()
    if ollama_connected:
        print("✓ Ollama connection verified")
        models = await ollama_service.list_models()
        print(f"  Available models: {len(models)}")
    else:
        print("✗ Ollama connection failed - make sure Ollama is running")
    
    print("=" * 50)

@app.get("/")
async def root():
    """Root endpoint - serves frontend or API info"""
    if FRONTEND_DIR.exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    return {
        "message": "McBOT API - Manufacturing Chatbot",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()
    ollama_status = await ollama_service.check_connection()
    
    return {
        "status": "healthy" if (db_status and ollama_status) else "degraded",
        "database": "connected" if db_status else "disconnected",
        "ollama": "connected" if ollama_status else "disconnected"
    }

@app.get("/api/models")
async def get_models(db: Session = Depends(get_db)):
    """Get all available Ollama models"""
    models = db.query(OllamaModel).filter(OllamaModel.is_enabled == True).all()
    return {
        "models": [
            {
                "id": m.model_id,
                "name": m.model_name,
                "display_name": m.display_name,
                "description": m.description,
                "size_gb": m.size_gb,
                "is_available": m.is_available
            }
            for m in models
        ]
    }

@app.get("/api/users/count")
async def get_user_count(db: Session = Depends(get_db)):
    """Get total user count"""
    count = db.query(User).count()
    return {"total_users": count}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

