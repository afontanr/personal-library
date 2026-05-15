from fastapi import APIRouter, Depends

from personal_library.application.use_cases.save_book import (
    SaveBookInput,
    SaveBookToCollection,
)
from personal_library.presentation.api.dependencies import get_save_book_use_case
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
