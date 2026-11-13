from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from personal_library.application.use_cases.list_collection import (
    CollectionOrder,
    ListCollection,
    group_by_saga,
)
from personal_library.application.use_cases.list_to_buy import ListToBuy
from personal_library.application.use_cases.lookup_book import (
    LookupBookByIsbn,
    to_isbn10,
    to_isbn13,
)
from personal_library.domain.exceptions import BookNotFoundError, BookRepositoryError
from personal_library.domain.model.collection_book import CollectionBook
from personal_library.domain.model.saga import SagaMembership
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.presentation.api.dependencies import (
    get_collection_repository,
    get_list_collection_use_case,
    get_list_to_buy_use_case,
    get_lookup_book_use_case,
)
from personal_library.presentation.web.formatting import format_volume

_WEB_DIR = FilePath(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_WEB_DIR / "templates"))
templates.env.filters["volume"] = format_volume

web_router = APIRouter()


class SimpleBook:
    """Lightweight object so Jinja2 can access attributes with dot notation."""

    def __init__(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


def _saga_data(saga: SagaMembership | None) -> dict | None:
    if saga is None:
        return None
    return {"name": saga.name, "volume": saga.volume}


def _saga_groups(books: list[CollectionBook]) -> list[dict] | None:
    """Groups for Orden por saga, or None when only the "Sin saga" group exists."""
    groups = group_by_saga(books)
    if all(group.name is None for group in groups):
        return None
    return [
        {"name": group.name, "books": _simple_books(group.books)} for group in groups
    ]


def _template_context(request: Request, **extra):
    return {"request": request, "current_year": datetime.now().year, **extra}


def _simple_books(books: list[CollectionBook]) -> list[SimpleBook]:
    return [
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
                "saga": _saga_data(b.saga),
            }
        )
        for b in books
    ]


@web_router.get("/", response_class=HTMLResponse, name="book_list")
async def book_list(
    request: Request,
    orden: str | None = None,
    use_case: ListCollection = Depends(get_list_collection_use_case),
):
    order = CollectionOrder.from_param(orden)
    books = await use_case.execute(order)
    groups = _saga_groups(books) if order is CollectionOrder.SAGA else None
    return templates.TemplateResponse(
        request,
        "book_list.html",
        _template_context(
            request, books=_simple_books(books), groups=groups, order=order.value
        ),
    )


@web_router.get("/futuras-compras", response_class=HTMLResponse, name="to_buy_list")
async def to_buy_list(
    request: Request,
    orden: str | None = None,
    use_case: ListToBuy = Depends(get_list_to_buy_use_case),
):
    order = CollectionOrder.from_param(orden)
    if order is CollectionOrder.SAGA:
        # Orden por saga only exists in the Colección.
        order = CollectionOrder.DEFAULT
    books = await use_case.execute(order)
    return templates.TemplateResponse(
        request,
        "to_buy_list.html",
        _template_context(request, books=_simple_books(books), order=order.value),
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
    lookup: LookupBookByIsbn = Depends(get_lookup_book_use_case),
):
    isbn_13 = to_isbn13(isbn)
    collection_book = await repo.find_by_isbn(isbn_13)

    if collection_book:
        simple_book = SimpleBook(
            {
                "isbn_13": collection_book.isbn_13,
                "isbn_10": collection_book.isbn_10,
                "title": collection_book.title,
                "authors": collection_book.authors,
                "description": collection_book.description,
                "published_date": collection_book.published_date,
                "cover_image_url": collection_book.cover_image_url,
                "status": collection_book.status,
                "rating": collection_book.rating,
                "tags": collection_book.tags,
                "opinion": collection_book.opinion,
                "reading_periods": [
                    {"start_date": rp.start_date, "end_date": rp.end_date}
                    for rp in collection_book.reading_periods
                ],
                "saga": _saga_data(collection_book.saga),
                "in_collection": True,
                "is_to_buy": collection_book.is_to_buy,
                "isbn_13_resolved": isbn_13,
            }
        )
    else:
        try:
            api_book = await lookup.execute(isbn)
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

        isbn_10 = api_book.isbn_10 or to_isbn10(isbn_13)

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
                "saga": None,
                "in_collection": False,
                "is_to_buy": False,
                "isbn_13_resolved": isbn_13,
            }
        )

    return templates.TemplateResponse(
        request,
        "book_detail.html",
        _template_context(request, book=simple_book),
    )


@web_router.get("/scan", response_class=HTMLResponse, name="scan")
async def scan(request: Request):
    return templates.TemplateResponse(
        request,
        "scan.html",
        _template_context(request),
    )
