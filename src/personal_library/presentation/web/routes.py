from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

_WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_WEB_DIR / "templates"))

web_router = APIRouter()

SAMPLE_BOOKS = [
    {
        "isbn_13": "9780060935467",
        "isbn_10": "0060935464",
        "title": "To Kill a Mockingbird",
        "authors": ["Harper Lee"],
        "description": (
            "The unforgettable novel of a childhood in a sleepy Southern town "
            "and the crisis of conscience that rocked it. 'To Kill A Mockingbird' "
            "became both an instant bestseller and a critical success when it was "
            "first published in 1960. It went on to win the Pulitzer Prize in 1961 "
            "and was later made into an Academy Award-winning film."
        ),
        "published_date": "1960-07-11",
        "cover_image_url": "https://books.google.com/books/content?id=PGR2AwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    },
    {
        "isbn_13": "9780451524935",
        "isbn_10": "0451524934",
        "title": "1984",
        "authors": ["George Orwell"],
        "description": (
            "Among the seminal texts of the 20th century, Nineteen Eighty-Four is "
            "a rare work that grows more haunting as its dystopian purgatory becomes "
            "more real. Published in 1949, the book offers political satirist George "
            "Orwell's nightmarish vision of a totalitarian, bureaucratic world."
        ),
        "published_date": "1949-06-08",
        "cover_image_url": "https://books.google.com/books/content?id=kotPYEqx7kMC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    },
    {
        "isbn_13": "9780743273565",
        "isbn_10": "0743273567",
        "title": "The Great Gatsby",
        "authors": ["F. Scott Fitzgerald"],
        "description": (
            "The Great Gatsby, F. Scott Fitzgerald's third book, stands as the "
            "supreme achievement of his career. This exemplary novel of the Jazz "
            "Age has been acclaimed by generations of readers."
        ),
        "published_date": "1925-04-10",
        "cover_image_url": "https://books.google.com/books/content?id=iXn5U2IzVH0C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    },
    {
        "isbn_13": "9780316769488",
        "isbn_10": "0316769487",
        "title": "The Catcher in the Rye",
        "authors": ["J.D. Salinger"],
        "description": (
            "The hero-Loss of Innocence and the Phoniness of the Adult World. "
            "Since his debut in 1951 as The Catcher in the Rye, Holden Caulfield "
            "has been synonymous with 'cynical adolescent'."
        ),
        "published_date": "1951-07-16",
        "cover_image_url": None,
    },
    {
        "isbn_13": "9780141439518",
        "isbn_10": "0141439513",
        "title": "Pride and Prejudice",
        "authors": ["Jane Austen"],
        "description": (
            "When Elizabeth Bennet first meets eligible bachelor Fitzwilliam Darcy, "
            "she thinks him arrogant and conceited; he is indifferent to her good "
            "looks and lively mind. When she later discovers that Darcy has "
            "involved himself in the troubled relationship between his friend "
            "Bingley and her beloved sister Jane, she is determined to dislike him "
            "more than ever."
        ),
        "published_date": "1813-01-28",
        "cover_image_url": "https://books.google.com/books/content?id=s1gVAAAAYAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api",
    },
    {
        "isbn_13": "9780547928227",
        "isbn_10": "0547928229",
        "title": "The Hobbit",
        "authors": ["J.R.R. Tolkien"],
        "description": (
            "A great modern classic and the prelude to The Lord of the Rings. "
            "Bilbo Baggins is a hobbit who enjoys a comfortable, unambitious life, "
            "rarely traveling any farther than his pantry or cellar. But his "
            "contentment is disturbed when the wizard Gandalf and a company of "
            "dwarves arrive on his doorstep."
        ),
        "published_date": "1937-09-21",
        "cover_image_url": "https://books.google.com/books/content?id=pD6arNyKyi8C&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    },
]


class SimpleBook:
    """Lightweight object so Jinja2 can access attributes with dot notation."""

    def __init__(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


def _get_books() -> list[SimpleBook]:
    return [SimpleBook(b) for b in SAMPLE_BOOKS]


def _find_book(isbn: str) -> SimpleBook | None:
    for b in SAMPLE_BOOKS:
        if b["isbn_13"] == isbn or b.get("isbn_10") == isbn:
            return SimpleBook(b)
    return None


@web_router.get("/", response_class=HTMLResponse, name="book_list")
async def book_list(request: Request):
    return templates.TemplateResponse(
        request,
        "book_list.html",
        {
            "books": _get_books(),
            "current_year": datetime.now().year,
        },
    )


@web_router.get("/book/{isbn}", response_class=HTMLResponse, name="book_detail")
async def book_detail(request: Request, isbn: str):
    book = _find_book(isbn)
    if not book:
        return HTMLResponse("<h1>Libro no encontrado</h1>", status_code=404)
    return templates.TemplateResponse(
        request,
        "book_detail.html",
        {
            "book": book,
            "current_year": datetime.now().year,
        },
    )
