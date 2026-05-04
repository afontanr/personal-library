from fastapi import APIRouter, Depends, HTTPException, Path

from personal_library.application.use_cases.lookup_book import LookupBookByIsbn
from personal_library.domain.exceptions import BookNotFoundError, BookRepositoryError
from personal_library.presentation.api.dependencies import get_lookup_book_use_case
from personal_library.presentation.api.schemas import BookInfoResponse

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/{isbn}", response_model=BookInfoResponse)
async def get_book(
    isbn: str = Path(pattern=r"^(\d{13}|\d{9}[\dXx])$"),
    use_case: LookupBookByIsbn = Depends(get_lookup_book_use_case),
) -> BookInfoResponse:
    try:
        book = await use_case.execute(isbn)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Book not found") from exc
    except BookRepositoryError as exc:
        raise HTTPException(status_code=502, detail="Upstream service error") from exc
    return BookInfoResponse(
        isbn_13=book.isbn_13,
        isbn_10=book.isbn_10,
        title=book.title,
        authors=book.authors,
        description=book.description,
        published_date=book.published_date,
        cover_image_url=book.cover_image_url,
    )
