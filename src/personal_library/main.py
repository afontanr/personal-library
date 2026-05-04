from fastapi import FastAPI

from personal_library.presentation.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Personal Library")
    app.include_router(api_router)
    return app


app = create_app()
