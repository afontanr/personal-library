from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from personal_library.infrastructure.adapters.db.sqlite_collection_repository import (
    SqliteCollectionRepository,
)
from personal_library.infrastructure.config.settings import Settings
from personal_library.presentation.api.router import api_router
from personal_library.presentation.web.routes import web_router

_STATIC_DIR = Path(__file__).resolve().parent / "presentation" / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    db_dir = Path(settings.database_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    collection_repo = SqliteCollectionRepository(
        database_path=settings.database_path
    )
    await collection_repo.initialize()
    app.state.collection_repository = collection_repo

    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield

    await collection_repo.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Library", lifespan=lifespan)
    app.mount(
        "/static",
        StaticFiles(directory=str(_STATIC_DIR)),
        name="web_static",
    )
    app.include_router(api_router)
    app.include_router(web_router)
    return app


app = create_app()
