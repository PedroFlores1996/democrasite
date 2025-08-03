from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.db.database import create_tables
from app.auth.routes import router as auth_router
from app.topics.routes import router as topics_router

app = FastAPI(
    title=settings.API_TITLE, 
    version=settings.API_VERSION,
    swagger_ui_parameters={
        "persistAuthorization": True  # Keep auth token across page refreshes
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with prefix
app.include_router(auth_router, prefix="/api")
app.include_router(topics_router, prefix="/api")

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve the frontend at root
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# Handle client-side routing (SPA) - this should be last
@app.get("/{path:path}")
async def serve_spa(path: str):
    # Serve index.html for any route that doesn't match API or static files
    if not path.startswith(("api", "docs", "redoc", "openapi.json", "static")):
        return FileResponse("frontend/index.html")
    # For other paths, let FastAPI handle normally
    raise HTTPException(status_code=404, detail="Not found")

create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)