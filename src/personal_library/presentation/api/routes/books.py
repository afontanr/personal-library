from fastapi import APIRouter, Depends, HTTPException

from personal_library.application.use_cases.lookup_book import LookupBookByIsbn
from personal_library.presentation.api.dependencies import get_lookup_book_use_case

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/{isbn}")
async def get_book(
    isbn: str,
    use_case: LookupBookByIsbn = Depends(get_lookup_book_use_case),
) -> dict:
    book = await use_case.execute(isbn)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "isbn_13": book.isbn_13,
        "isbn_10": book.isbn_10,
        "title": book.title,
        "authors": book.authors,
        "description": book.description,
        "published_date": book.published_date,
        "cover_image_url": book.cover_image_url,
    }
