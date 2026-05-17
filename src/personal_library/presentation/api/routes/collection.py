from fastapi import APIRouter, Depends, HTTPException, Path

from personal_library.application.use_cases.delete_book import (
    DeleteBookFromCollection,
)
from personal_library.application.use_cases.save_book import (
    SaveBookInput,
    SaveBookToCollection,
)
from personal_library.domain.exceptions import BookNotFoundError
from personal_library.domain.ports.collection_repository import CollectionRepository
from personal_library.presentation.api.dependencies import (
    get_collection_repository,
    get_delete_book_use_case,
    get_save_book_use_case,
)
from personal_library.presentation.api.schemas import (
    CollectionBookResponse,
    ReadingPeriodRequest,
    SaveBookRequest,
)

router = APIRouter(prefix="/api/collection", tags=["collection"])


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
    )
    result = await use_case.execute(book_input)
    return CollectionBookResponse(
        isbn_13=result.isbn_13,
        isbn_10=result.isbn_10,
        title=result.title,
        authors=result.authors,
        description=result.description,
        published_date=result.published_date,
        cover_image_url=result.cover_image_url,
        status=result.status,
        rating=result.rating,
        tags=result.tags,
        opinion=result.opinion,
        added_at=result.added_at,
        reading_periods=[
            ReadingPeriodRequest(
                start_date=rp.start_date,
                end_date=rp.end_date,
            )
            for rp in result.reading_periods
        ],
    )


@router.get("", response_model=list[CollectionBookResponse])
async def list_collection(
    repo: CollectionRepository = Depends(get_collection_repository),
) -> list[CollectionBookResponse]:
    books = await repo.find_all()
    return [
        CollectionBookResponse(
            isbn_13=b.isbn_13,
            isbn_10=b.isbn_10,
            title=b.title,
            authors=b.authors,
            description=b.description,
            published_date=b.published_date,
            cover_image_url=b.cover_image_url,
            status=b.status,
            rating=b.rating,
            tags=b.tags,
            opinion=b.opinion,
            added_at=b.added_at,
            reading_periods=[
                ReadingPeriodRequest(
                    start_date=rp.start_date,
                    end_date=rp.end_date,
                )
                for rp in b.reading_periods
            ],
        )
        for b in books
    ]


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
