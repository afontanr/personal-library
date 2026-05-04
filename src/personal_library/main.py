from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from personal_library.presentation.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        yield


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Library", lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_app()
