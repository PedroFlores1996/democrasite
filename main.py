from fastapi import FastAPI

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

app.include_router(auth_router)
app.include_router(topics_router)

create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)