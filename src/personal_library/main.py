from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from personal_library.presentation.api.router import api_router
from personal_library.presentation.web.routes import web_router

_STATIC_DIR = Path(__file__).resolve().parent / "presentation" / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


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
