from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from personal_library.application.use_cases.save_book import SaveBookInput
from personal_library.infrastructure.adapters.db.sqlite_collection_repository import (
    SqliteCollectionRepository,
)
from personal_library.infrastructure.config.settings import Settings
from personal_library.presentation.api.router import api_router
from personal_library.presentation.web.routes import web_router

_STATIC_DIR = Path(__file__).resolve().parent / "presentation" / "web" / "static"

_SAMPLE_BOOKS = [
    {
        "isbn_13": "9780060935467",
        "isbn_10": "0060935464",
        "title": "To Kill a Mockingbird",
        "authors": ["Harper Lee"],
        "description": (
            "The unforgettable novel of a childhood in a sleepy Southern town "
            "and the crisis of conscience that rocked it."
        ),
        "published_date": "1960-07-11",
        "cover_image_url": "https://books.google.com/books/content?id=PGR2AwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
        "status": "read",
        "rating": 5.0,
        "tags": ["fiction", "classic"],
        "opinion": "A masterpiece of American literature.",
    },
    {
        "isbn_13": "9780451524935",
        "isbn_10": "0451524934",
        "title": "1984",
        "authors": ["George Orwell"],
        "description": (
            "Among the seminal texts of the 20th century, Nineteen Eighty-Four is "
            "a rare work that grows more haunting as its dystopian purgatory becomes "
            "more real."
        ),
        "published_date": "1949-06-08",
        "cover_image_url": "https://books.google.com/books/content?id=kotPYEqx7kMC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
        "status": "read",
        "rating": 4.5,
        "tags": ["fiction", "dystopian"],
        "opinion": "Orwell's vision remains terrifyingly relevant.",
    },
    {
        "isbn_13": "9780743273565",
        "isbn_10": "0743273567",
        "title": "The Great Gatsby",
        "authors": ["F. Scott Fitzgerald"],
        "description": (
            "The Great Gatsby, F. Scott Fitzgerald's third book, stands as the "
            "supreme achievement of his career."
        ),
        "published_date": "1925-04-10",
        "cover_image_url": "https://books.google.com/books/content?id=iXn5U2IzVH0C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
        "status": "pending",
        "rating": None,
        "tags": ["fiction", "classic"],
        "opinion": None,
    },
    {
        "isbn_13": "9780316769488",
        "isbn_10": "0316769487",
        "title": "The Catcher in the Rye",
        "authors": ["J.D. Salinger"],
        "description": (
            "The hero-Loss of Innocence and the Phoniness of the Adult World."
        ),
        "published_date": "1951-07-16",
        "cover_image_url": None,
        "status": "new",
        "rating": None,
        "tags": [],
        "opinion": None,
    },
    {
        "isbn_13": "9780141439518",
        "isbn_10": "0141439513",
        "title": "Pride and Prejudice",
        "authors": ["Jane Austen"],
        "description": (
            "When Elizabeth Bennet first meets eligible bachelor Fitzwilliam Darcy, "
            "she thinks him arrogant and conceited."
        ),
        "published_date": "1813-01-28",
        "cover_image_url": "https://books.google.com/books/content?id=s1gVAAAAYAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api",
        "status": "next_up",
        "rating": None,
        "tags": ["fiction", "romance", "classic"],
        "opinion": None,
    },
    {
        "isbn_13": "9780547928227",
        "isbn_10": "0547928229",
        "title": "The Hobbit",
        "authors": ["J.R.R. Tolkien"],
        "description": (
            "A great modern classic and the prelude to The Lord of the Rings."
        ),
        "published_date": "1937-09-21",
        "cover_image_url": "https://books.google.com/books/content?id=pD6arNyKyi8C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
        "status": "reading",
        "rating": None,
        "tags": ["fantasy", "classic"],
        "opinion": None,
    },
]


async def _seed_sample_data(repo: SqliteCollectionRepository) -> None:
    existing = await repo.find_all()
    if existing:
        return

    from personal_library.application.use_cases.save_book import SaveBookToCollection

    use_case = SaveBookToCollection(collection_repository=repo)

    for book_data in _SAMPLE_BOOKS:
        await use_case.execute(
            SaveBookInput(
                isbn_13=book_data["isbn_13"],
                isbn_10=book_data["isbn_10"],
                title=book_data["title"],
                authors=book_data["authors"],
                description=book_data["description"],
                published_date=book_data["published_date"],
                cover_image_url=book_data["cover_image_url"],
                status=book_data["status"],
                rating=book_data["rating"],
                tags=book_data["tags"],
                opinion=book_data["opinion"],
            )
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    db_dir = Path(settings.database_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    collection_repo = SqliteCollectionRepository(
        database_path=settings.database_path
    )
    await collection_repo.initialize()
    await _seed_sample_data(collection_repo)
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
