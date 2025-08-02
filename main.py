from fastapi import FastAPI

from app.config.settings import settings
from app.db.database import create_tables
from app.api.routes import router

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

app.include_router(router)

create_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)