from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.presentation.api.dependencies import get_collection_repository

_WEB_DIR = FilePath(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_WEB_DIR / "templates"))

web_router = APIRouter()


class SimpleBook:
    """Lightweight object so Jinja2 can access attributes with dot notation."""

    def __init__(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


def _template_context(request: Request, **extra):
    return {"request": request, "current_year": datetime.now().year, **extra}


@web_router.get("/", response_class=HTMLResponse, name="book_list")
async def book_list(
    request: Request,
    repo: CollectionRepository = Depends(get_collection_repository),
):
    books = await repo.find_all()
    simple_books = [
        SimpleBook(
            {
                "isbn_13": b.isbn_13,
                "isbn_10": b.isbn_10,
                "title": b.title,
                "authors": b.authors,
                "description": b.description,
                "published_date": b.published_date,
                "cover_image_url": b.cover_image_url,
                "status": b.status,
                "rating": b.rating,
                "tags": b.tags,
                "opinion": b.opinion,
            }
        )
        for b in books
    ]
    return templates.TemplateResponse(
        request,
        "book_list.html",
        _template_context(request, books=simple_books),
    )


@web_router.get(
    "/book/{isbn}",
    response_class=HTMLResponse,
    name="book_detail",
)
async def book_detail(
    request: Request,
    isbn: str = Path(pattern=r"^(\d{13}|\d{9}[\dXx])$"),
    repo: CollectionRepository = Depends(get_collection_repository),
):
    from personal_library.application.use_cases.lookup_book import (
        _to_isbn10,
        _to_isbn13,
    )
    from personal_library.domain.ports.book_repository import BookRepository
    from personal_library.presentation.api.dependencies import get_book_repository

    isbn_13 = _to_isbn13(isbn)
    book = await repo.find_by_isbn(isbn_13)

    if book:
        simple_book = SimpleBook(
            {
                "isbn_13": book.isbn_13,
                "isbn_10": book.isbn_10,
                "title": book.title,
                "authors": book.authors,
                "description": book.description,
                "published_date": book.published_date,
                "cover_image_url": book.cover_image_url,
                "status": book.status,
                "rating": book.rating,
                "tags": book.tags,
                "opinion": book.opinion,
                "reading_periods": [
                    {"start_date": rp.start_date, "end_date": rp.end_date}
                    for rp in book.reading_periods
                ],
                "in_collection": True,
                "isbn_13_resolved": isbn_13,
            }
        )
    else:
        from personal_library.domain.exceptions import (
            BookNotFoundError,
            BookRepositoryError,
        )

        book_repo: BookRepository = get_book_repository(request)
        try:
            api_book = await book_repo.find_by_isbn(isbn_13)
        except BookNotFoundError:
            return templates.TemplateResponse(
                request,
                "404.html",
                _template_context(request),
                status_code=404,
            )
        except BookRepositoryError:
            return templates.TemplateResponse(
                request,
                "404.html",
                _template_context(request),
                status_code=404,
            )

        isbn_10 = api_book.isbn_10 or _to_isbn10(isbn_13)

        simple_book = SimpleBook(
            {
                "isbn_13": isbn_13,
                "isbn_10": isbn_10,
                "title": api_book.title,
                "authors": api_book.authors,
                "description": api_book.description,
                "published_date": api_book.published_date,
                "cover_image_url": api_book.cover_image_url,
                "status": "new",
                "rating": None,
                "tags": [],
                "opinion": None,
                "reading_periods": [],
                "in_collection": False,
                "isbn_13_resolved": isbn_13,
            }
        )

    return templates.TemplateResponse(
        request,
        "book_detail.html",
        _template_context(request, book=simple_book),
    )
