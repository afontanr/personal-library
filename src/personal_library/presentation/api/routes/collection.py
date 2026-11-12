from fastapi import APIRouter, Depends, HTTPException, Path

from personal_library.application.use_cases.delete_book import (
    DeleteBookFromCollection,
)
from personal_library.application.use_cases.list_collection import (
    CollectionOrder,
    ListCollection,
)
from personal_library.application.use_cases.save_book import (
    SaveBookInput,
    SaveBookToCollection,
)
from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.model.collection_book import CollectionBook
from personal_library.presentation.api.dependencies import (
    get_delete_book_use_case,
    get_list_collection_use_case,
    get_save_book_use_case,
)
from personal_library.presentation.api.schemas import (
    CollectionBookResponse,
    ReadingPeriodRequest,
    SagaResponse,
    SaveBookRequest,
)

router = APIRouter(prefix="/api/collection", tags=["collection"])


def _to_response(book: CollectionBook) -> CollectionBookResponse:
    return CollectionBookResponse(
        isbn_13=book.isbn_13,
        isbn_10=book.isbn_10,
        title=book.title,
        authors=book.authors,
        description=book.description,
        published_date=book.published_date,
        cover_image_url=book.cover_image_url,
        status=book.status,
        rating=book.rating,
        tags=book.tags,
        opinion=book.opinion,
        added_at=book.added_at,
        reading_periods=[
            ReadingPeriodRequest(start_date=rp.start_date, end_date=rp.end_date)
            for rp in book.reading_periods
        ],
        saga=(
            SagaResponse(
                id=book.saga.saga_id, name=book.saga.name, volume=book.saga.volume
            )
            if book.saga
            else None
        ),
    )


@router.post("", status_code=201, response_model=CollectionBookResponse)
async def save_book(
    body: SaveBookRequest,
    use_case: SaveBookToCollection = Depends(get_save_book_use_case),
) -> CollectionBookResponse:
    book_input = SaveBookInput(
        isbn_13=body.isbn_13,
        isbn_10=body.isbn_10,
        title=body.title,
        authors=body.authors,
        description=body.description,
        published_date=body.published_date,
        cover_image_url=body.cover_image_url,
        status=body.status,
        rating=body.rating,
        tags=body.tags,
        opinion=body.opinion,
        reading_periods=[
            SaveBookInput.ReadingPeriodInput(
                start_date=rp.start_date,
                end_date=rp.end_date,
            )
            for rp in body.reading_periods
        ],
        saga=(
            SaveBookInput.SagaInput(name=body.saga.name, volume=body.saga.volume)
            if body.saga
            else None
        ),
    )
    try:
        result = await use_case.execute(book_input)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_response(result)


@router.get("", response_model=list[CollectionBookResponse])
async def list_collection(
    orden: str | None = None,
    use_case: ListCollection = Depends(get_list_collection_use_case),
) -> list[CollectionBookResponse]:
    books = await use_case.execute(CollectionOrder.from_param(orden))
    return [_to_response(b) for b in books]


@router.delete(
    "/{isbn}",
    status_code=204,
    responses={404: {"description": "Book not found"}},
)
async def delete_book(
    isbn: str = Path(pattern=r"^(\d{13}|\d{9}[\dXx])$"),
    use_case: DeleteBookFromCollection = Depends(get_delete_book_use_case),
):
    try:
        await use_case.execute(isbn)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Book not found") from exc
